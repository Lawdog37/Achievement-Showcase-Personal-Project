"""
Usage (from the backend folder):
    python -m app.sync                  # sync only games that changed since last time
    python -m app.sync --force          # re-sync every game
    python -m app.sync --game 1172620   # sync one game
"""

import argparse
import logging
import time
from collections import Counter
from datetime import datetime, timedelta, timezone

from app import steam_client as steam
from app.config import STEAM_ID
from app.database import SessionLocal
from app.models import Achievement, Game, Player, PlayerAchievement, PlayerGame

logger = logging.getLogger(__name__)

ICON_BASE = "https://media.steampowered.com/steamcommunity/public/images/apps"
PERCENTAGES_MAX_AGE = timedelta(days=1)  # rarity changes slowly
DELAY_BETWEEN_GAMES = 0.5  # seconds: be polite to Steam's servers


class SyncError(Exception):
    """A problem that stops the whole sync, like a private profile."""


# --- Time helpers --------------------------------------------------------
def now_utc():
    return datetime.now(timezone.utc)


def to_datetime(unix_seconds):
    """Steam sends times as seconds since 1970. 0 means 'no time'."""
    if not unix_seconds:
        return None
    return datetime.fromtimestamp(unix_seconds, tz = timezone.utc)


def as_utc(value):
    """SQLite forgets time zones when it saves, so label stored times as UTC."""
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo = timezone.utc)


# --- Saving each kind of row ---------------------------------------------
def save_player(session, steam_id):
    summary = steam.get_player_summary(steam_id)
    if summary is None:
        raise SyncError(f"No Steam user has the id {steam_id}")
    if summary.get("communityvisibilitystate") != 3:  # 3 means public
        raise SyncError("This Steam profile is private. Set it to Public.")
    return session.merge(
        Player(
            steam_id=steam_id,
            name = summary["personaname"],
            avatar_url = summary.get("avatarfull"),
        )
    )


def save_game(session, info):
    """Insert or update a game. Returns the Game row."""
    game = session.get(Game, info["appid"])
    if game is None:
        game = Game(app_id=info["appid"])
        session.add(game)
    game.name = info["name"]
    icon_hash = info.get("img_icon_url")
    game.icon_url = f"{ICON_BASE}/{game.app_id}/{icon_hash}.jpg" if icon_hash else None
    return game


def save_player_game(session, steam_id, info):
    """Insert or update 'this player owns this game'. Returns the PlayerGame row."""
    player_game = session.get(PlayerGame, (steam_id, info["appid"]))
    if player_game is None:
        player_game = PlayerGame(steam_id=steam_id, app_id=info["appid"])
        session.add(player_game)
    player_game.playtime_minutes = info.get("playtime_forever", 0)
    player_game.last_played_at = to_datetime(info.get("rtime_last_played"))
    return player_game


def needs_sync(game, player_game, playtime, force):
    """Decide whether this game's achievements must be fetched again."""
    if force:
        return True
    if playtime == 0:
        return False  # never played, so nothing can be unlocked
    if game.has_achievements is False:
        return False  # we checked before: this game has none
    synced_at = as_utc(player_game.achievements_synced_at)
    if synced_at is None:
        return True  # never synced
    last_played = as_utc(player_game.last_played_at)
    return last_played is not None and last_played > synced_at  # played since


def save_achievements(session, steam_id, game):
    """Fetch and save one game's achievements. Returns unlocked"""
    schema = steam.get_schema(game.app_id)
    game.has_achievements = bool(schema)
    if not schema:
        return 0

    for a in schema:
        # merge() only updates the fields we pass, so global_percent is kept
        session.merge(
            Achievement(
                app_id = game.app_id,
                api_name = a["name"],
                display_name = a["displayName"],
                description = a.get("description"),
                icon_url = a.get("icon"),
                icon_gray_url = a.get("icongray"),
                hidden = bool(a.get("hidden", 0)),
            )
        )
    session.flush()  # achievements must exist before unlocks can point at them

    updated_at = as_utc(game.percentages_updated_at)
    if updated_at is None or now_utc() - updated_at > PERCENTAGES_MAX_AGE:
        for api_name, percent in steam.get_global_percentages(game.app_id).items():
            achievement = session.get(Achievement, (game.app_id, api_name))
            if achievement is not None:
                achievement.global_percent = percent
        game.percentages_updated_at = now_utc()

    known = {a["name"] for a in schema}
    unlocked = [
        a
        for a in steam.get_player_achievements(steam_id, game.app_id)
        if a["achieved"] == 1 and a["apiname"] in known
    ]
    for a in unlocked:
        session.merge(
            PlayerAchievement(
                steam_id = steam_id,
                app_id = game.app_id,
                api_name = a["apiname"],
                unlocked_at=to_datetime(a["unlocktime"]),
            )
        )
    return len(unlocked)


# --- The whole sync ------------------------------------------------------
def sync_player(steam_id, force=False, only_app_id=None):
    """Sync a player's games and achievements. Returns a summary dict."""
    started = time.monotonic()
    counts = Counter()

    with SessionLocal() as session:
        player = save_player(session, steam_id)
        owned = steam.get_owned_games(steam_id)
        if not owned:
            raise SyncError("No games found. Is 'Game details' set to Public?")
        if only_app_id is not None:
            owned = [g for g in owned if g["appid"] == only_app_id]
            if not owned:
                raise SyncError(f"You don't own a game with appid {only_app_id}")
            force = True
        session.commit()

        total = len(owned)
        for number, info in enumerate(owned, start=1):
            label = f"[{number}/{total}] {info['name']}"
            try:
                game = save_game(session, info)
                player_game = save_player_game(session, steam_id, info)
                session.flush()

                if not needs_sync(game, player_game, info.get("playtime_forever", 0), force):
                    counts["skipped"] += 1
                    session.commit()
                    continue

                unlocked = save_achievements(session, steam_id, game)
                player_game.achievements_synced_at = now_utc()
                session.commit()  # save each game as we go
                counts["synced"] += 1
                if game.has_achievements:
                    logger.info("%s: %d unlocked", label, unlocked)
                else:
                    logger.info("%s: no achievements", label)
                time.sleep(DELAY_BETWEEN_GAMES)
            except (steam.SteamAPIError, KeyError, ValueError) as error:
                session.rollback()  # undo this game's half-finished changes
                counts["failed"] += 1
                logger.warning("%s: failed (%s)", label, error)

        player.last_synced_at = now_utc()
        session.commit()

    return {
        "games": total,
        "synced": counts["synced"],
        "skipped": counts["skipped"],
        "failed": counts["failed"],
        "seconds": round(time.monotonic() - started, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Sync Steam achievements into the database.")
    parser.add_argument("--force", action="store_true", help="re-sync every game")
    parser.add_argument("--game", type=int, help="only sync this appid")
    parser.add_argument("--steam-id", default=STEAM_ID, help="defaults to STEAM_ID in .env")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )
    # httpx logs every URL at INFO level, and our URLs contain the API key
    logging.getLogger("httpx").setLevel(logging.WARNING)

    try:
        summary = sync_player(args.steam_id, force=args.force, only_app_id=args.game)
    except SyncError as error:
        raise SystemExit(f"Sync failed: {error}")
    print(
        f"\nDone in {summary['seconds']}s: {summary['synced']} synced, "
        f"{summary['skipped']} unchanged, {summary['failed']} failed "
        f"(out of {summary['games']} games)"
    )


if __name__ == "__main__":
    main()