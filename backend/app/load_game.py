"""Load one game's achievements into the database.

Usage (from the backend folder):  python -m app.load_game 1172620
"""

import sys
from datetime import datetime, timezone

from app import steam_client as steam
from app.config import STEAM_ID
from app.database import SessionLocal
from app.models import Achievement, Game, Player, PlayerAchievement, PlayerGame

ICON_BASE = "https://media.steampowered.com/steamcommunity/public/images/apps"


def to_datetime(unix_seconds):
    """Steam sends times as seconds since 1970. 0 means 'no time'."""
    if not unix_seconds:
        return None
    return datetime.fromtimestamp(unix_seconds, tz=timezone.utc)


def load_game(steam_id, app_id):
    # 1. Fetch everything from Steam first
    summary = steam.get_player_summary(steam_id)
    owned = {g["appid"]: g for g in steam.get_owned_games(steam_id)}
    if app_id not in owned:
        print(f"Skipping {app_id}: you don't own it")
        return
    game_info = owned[app_id]
    schema = steam.get_schema(app_id)
    if not schema:
        print(f"Skipping {game_info['name']}: it has no achievements")
        return
    percentages = steam.get_global_percentages(app_id)
    player_achievements = steam.get_player_achievements(steam_id, app_id)

    # 2. Save it. merge() = insert the row, or update it if it already exists
    with SessionLocal() as session:
        session.merge(
            Player(
                steam_id=steam_id,
                name=summary["personaname"],
                avatar_url=summary.get("avatarfull"),
                last_synced_at=datetime.now(timezone.utc),
            )
        )
        icon_hash = game_info.get("img_icon_url")
        session.merge(
            Game(
                app_id=app_id,
                name=game_info["name"],
                icon_url=f"{ICON_BASE}/{app_id}/{icon_hash}.jpg" if icon_hash else None,
            )
        )
        session.flush()  # write parents first so foreign keys are satisfied

        session.merge(
            PlayerGame(
                steam_id=steam_id,
                app_id=app_id,
                playtime_minutes=game_info.get("playtime_forever", 0),
                last_played_at=to_datetime(game_info.get("rtime_last_played")),
            )
        )
        for a in schema:
            session.merge(
                Achievement(
                    app_id=app_id,
                    api_name=a["name"],
                    display_name=a["displayName"],
                    description=a.get("description"),  # hidden ones may have none
                    icon_url=a.get("icon"),
                    icon_gray_url=a.get("icongray"),
                    hidden=bool(a.get("hidden", 0)),
                    global_percent=percentages.get(a["name"]),
                )
            )
        session.flush()

        unlocked = [a for a in player_achievements if a["achieved"] == 1]
        for a in unlocked:
            session.merge(
                PlayerAchievement(
                    steam_id=steam_id,
                    app_id=app_id,
                    api_name=a["apiname"],
                    unlocked_at=to_datetime(a["unlocktime"]),
                )
            )
        session.commit()

    print(f"Saved {game_info['name']}: {len(schema)} achievements, {len(unlocked)} unlocked")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python -m app.load_game <appid> [<appid> ...]")
    for arg in sys.argv[1:]:
        load_game(STEAM_ID, int(arg))