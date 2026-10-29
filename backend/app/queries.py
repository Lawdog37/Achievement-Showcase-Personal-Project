"""Questions we ask the database, written with SQLAlchemy.

Try it (from the backend folder):  python -m app.queries
"""

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from statistics import mean

from sqlalchemy import Numeric, and_, cast, func, select

from app.config import STEAM_ID
from app.database import SessionLocal
from app.models import (
    Achievement,
    ChartEntry,
    Game,
    GameSnapshot,
    Hunt,
    PlayerAchievement,
    PlayerGame,
)


def rarest_unlocked(session, steam_id, limit=10):
    """Your unlocked achievements, rarest first."""
    stmt = (
        select(
            Achievement.app_id,
            Game.name.label("game_name"),
            Achievement.api_name,
            Achievement.display_name,
            Achievement.description,
            Achievement.icon_url,
            Achievement.global_percent,
            PlayerAchievement.unlocked_at,
        )
        .join(
            Achievement,
            (Achievement.app_id == PlayerAchievement.app_id)
            & (Achievement.api_name == PlayerAchievement.api_name),
        )
        .join(Game, Game.app_id == PlayerAchievement.app_id)
        .where(PlayerAchievement.steam_id == steam_id)
        .where(Achievement.global_percent.is_not(None))
        .order_by(Achievement.global_percent, PlayerAchievement.unlocked_at)
        .limit(limit)
    )
    return session.execute(stmt).all()


def _owned_achievements(steam_id, *columns):
    """Every achievement in every game the player owns, plus their unlock row
    if they have one (LEFT JOIN). The starting point for progress queries."""
    return (
        select(*columns)
        .select_from(PlayerGame)
        .join(Game, Game.app_id == PlayerGame.app_id)
        .join(Achievement, Achievement.app_id == PlayerGame.app_id)
        .outerjoin(
            PlayerAchievement,
            and_(
                PlayerAchievement.steam_id == PlayerGame.steam_id,
                PlayerAchievement.app_id == Achievement.app_id,
                PlayerAchievement.api_name == Achievement.api_name,
            ),
        )
        .where(PlayerGame.steam_id == steam_id)
    )


# Reusable pieces for the per-game counts
TOTAL = func.count(Achievement.api_name)
UNLOCKED = func.count(PlayerAchievement.api_name)
# Postgres can only round exact decimals (Numeric), not floats, so convert first
PCT = func.round(cast(100.0 * UNLOCKED / TOTAL, Numeric), 1)


def _completion_query(steam_id):
    return (
        _owned_achievements(
            steam_id,
            Game.app_id,
            Game.name,
            Game.icon_url,
            TOTAL.label("total"),
            UNLOCKED.label("unlocked"),
            PCT.label("pct"),
        )
        .group_by(Game.app_id, Game.name, Game.icon_url)
        .order_by(PCT.desc(), Game.name)
    )


def completion_by_game(session, steam_id):
    """How many achievements you have in each game, and the percentage."""
    return session.execute(_completion_query(steam_id)).all()


def games_in_progress(session, steam_id, limit=10):
    """Started but not finished, closest to 100% first."""
    stmt = _completion_query(steam_id).having(UNLOCKED > 0).having(UNLOCKED < TOTAL).limit(limit)
    return session.execute(stmt).all()


def player_games(session, steam_id, status="in_progress", sort="percent", app_ids=None):
    """Every owned game that has achievements, with its completion"""
    remaining = TOTAL - UNLOCKED
    stmt = _owned_achievements(
        steam_id,
        Game.app_id,
        Game.name,
        Game.icon_url,
        PlayerGame.playtime_minutes,
        PlayerGame.last_played_at,
        TOTAL.label("total"),
        UNLOCKED.label("unlocked"),
        remaining.label("remaining"),
        PCT.label("pct"),
    ).group_by(
        Game.app_id,
        Game.name,
        Game.icon_url,
        PlayerGame.playtime_minutes,
        PlayerGame.last_played_at,
    )
    if app_ids is not None:  # only these games (used by the Hunting page)
        stmt = stmt.where(PlayerGame.app_id.in_(app_ids))
    # HAVING filters on the counts, after GROUP BY has done the counting
    if status == "in_progress":
        stmt = stmt.having(UNLOCKED > 0).having(UNLOCKED < TOTAL)
    elif status == "completed":
        stmt = stmt.having(UNLOCKED == TOTAL)
    elif status == "not_started":
        stmt = stmt.having(UNLOCKED == 0)

    order_by = {
        "percent": [PCT.desc(), Game.name],
        "remaining": [remaining, Game.name],
        "name": [Game.name],
        "recent": [PlayerGame.last_played_at.desc().nulls_last(), Game.name],
    }[sort]
    return session.execute(stmt.order_by(*order_by)).all()


def player_hunts(session, steam_id):
    """The games a player is hunting, each with every achievement still locked."""
    added = dict(
        session.execute(select(Hunt.app_id, Hunt.added_at).where(Hunt.steam_id == steam_id)).all()
    )
    if not added:
        return []

    games = player_games(session, steam_id, status="all", app_ids=list(added))
    locked_rows = session.execute(
        _owned_achievements(
            steam_id,
            Achievement.app_id,
            Achievement.api_name,
            Achievement.display_name,
            Achievement.description,
            Achievement.icon_gray_url,
            Achievement.hidden,
            Achievement.global_percent,
        )
        .where(PlayerGame.app_id.in_(list(added)))
        .where(PlayerAchievement.api_name.is_(None))  # still locked
        .order_by(Achievement.global_percent.desc().nulls_last(), Achievement.display_name)
    ).all()

    # Group the locked achievements by game: {app_id: [row, row, ...]}
    locked = defaultdict(list)
    for row in locked_rows:
        locked[row.app_id].append(row)

    return [
        {"game": game, "added_at": added[game.app_id], "locked": locked[game.app_id]}
        for game in games
    ]


def next_easiest(session, steam_id, limit=5):
    """Locked achievements that the most players have, so the easiest to get next."""
    stmt = (
        _owned_achievements(
            steam_id,
            Achievement.app_id,
            Game.name.label("game_name"),
            Achievement.api_name,
            Achievement.display_name,
            Achievement.description,
            Achievement.icon_gray_url,
            Achievement.global_percent,
        )
        .where(PlayerAchievement.api_name.is_(None))  # no unlock row = locked
        .where(Achievement.global_percent.is_not(None))
        .order_by(Achievement.global_percent.desc())
        .limit(limit)
    )
    return session.execute(stmt).all()


def player_stats(session, steam_id):
    """Headline numbers for a player's profile page."""
    games = completion_by_game(session, steam_id)
    started = [g for g in games if g.unlocked > 0]

    games_owned = session.scalar(
        select(func.count()).select_from(PlayerGame).where(PlayerGame.steam_id == steam_id)
    )
    minutes = session.scalar(
        select(func.coalesce(func.sum(PlayerGame.playtime_minutes), 0)).where(
            PlayerGame.steam_id == steam_id
        )
    )
    unlock_times = session.scalars(
        select(PlayerAchievement.unlocked_at).where(
            PlayerAchievement.steam_id == steam_id,
            PlayerAchievement.unlocked_at.is_not(None),
        )
    ).all()
    # Grouping by month in Python works the same on SQLite and Postgres
    per_month = Counter(t.strftime("%Y-%m") for t in unlock_times)

    return {
        "games_owned": games_owned,
        "games_with_achievements": len(games),
        "games_started": len(started),
        "perfect_games": sum(1 for g in started if g.unlocked == g.total),
        "achievements_unlocked": sum(g.unlocked for g in games),
        "achievements_total": sum(g.total for g in games),
        "average_completion": round(mean(g.pct for g in started), 1) if started else 0.0,
        "hours_played": round(minutes / 60, 1),
        "unlocks_by_month": [{"month": m, "count": per_month[m]} for m in sorted(per_month)],
    }


# --- Overview page -------------------------------------------------------
def most_played(session):
    """The latest saved chart, with each game's rarest achievement %.
    Returns (chart_date, rows), or (None, []) before the first chart is saved."""
    chart_date = session.scalar(select(func.max(ChartEntry.taken_on)))
    if chart_date is None:
        return None, []

    # Each game's newest snapshot date, joined back to get that snapshot's numbers
    newest = (
        select(GameSnapshot.app_id, func.max(GameSnapshot.taken_on).label("taken_on"))
        .group_by(GameSnapshot.app_id)
        .subquery()
    )
    stmt = (
        select(
            ChartEntry.rank,
            ChartEntry.last_week_rank,
            ChartEntry.peak_players,
            Game.app_id,
            Game.name,
            func.coalesce(Game.capsule_url, Game.icon_url).label("image_url"),
            Game.has_achievements,
            GameSnapshot.rarest_percent,
            GameSnapshot.achievement_count,
        )
        .join(Game, Game.app_id == ChartEntry.app_id)
        .outerjoin(newest, newest.c.app_id == ChartEntry.app_id)
        .outerjoin(
            GameSnapshot,
            and_(
                GameSnapshot.app_id == newest.c.app_id,
                GameSnapshot.taken_on == newest.c.taken_on,
            ),
        )
        .where(ChartEntry.taken_on == chart_date)
        .order_by(ChartEntry.rank)
    )
    return chart_date, session.execute(stmt).all()


def trending_games(session, days=7, limit=10):
    """Games whose rarest achievement is being unlocked by a growing share of
    players over the last `days` days: a sign more people are finishing them."""
    since = datetime.now(UTC).date() - timedelta(days=days)
    rows = session.execute(
        select(GameSnapshot.app_id, GameSnapshot.taken_on, GameSnapshot.rarest_percent)
        .where(GameSnapshot.taken_on >= since)
        .order_by(GameSnapshot.app_id, GameSnapshot.taken_on)
    ).all()

    # Rows are sorted by game then date, so the first and last per game
    # are its oldest and newest snapshots in the window
    oldest, newest = {}, {}
    for row in rows:
        oldest.setdefault(row.app_id, row)
        newest[row.app_id] = row

    rising = []
    for app_id, new in newest.items():
        old = oldest[app_id]
        change = new.rarest_percent - old.rarest_percent
        if new.taken_on > old.taken_on and change > 0:
            rising.append((change, old, new))
    rising.sort(key=lambda item: item[0], reverse=True)
    rising = rising[:limit]

    ids = [new.app_id for _, _, new in rising]
    games = {
        game.app_id: game for game in session.scalars(select(Game).where(Game.app_id.in_(ids)))
    }
    return [
        {
            "app_id": new.app_id,
            "name": games[new.app_id].name,
            "image_url": games[new.app_id].capsule_url or games[new.app_id].icon_url,
            "rarest_before": old.rarest_percent,
            "rarest_now": new.rarest_percent,
            "change": round(change, 2),
            "days": (new.taken_on - old.taken_on).days,
        }
        for change, old, new in rising
    ]


def snapshot_days(session):
    """How many different days we have snapshots for."""
    return session.scalar(select(func.count(func.distinct(GameSnapshot.taken_on))))


if __name__ == "__main__":
    with SessionLocal() as session:
        print("Your rarest achievements:")
        for row in rarest_unlocked(session, STEAM_ID):
            print(f"  {row.global_percent:5.1f}%  {row.display_name:<35} {row.game_name}")

        print("\nClosest to 100%:")
        for row in games_in_progress(session, STEAM_ID, limit=5):
            print(f"  {row.pct:5.1f}%  {row.unlocked:>4}/{row.total:<4} {row.name}")

        print("\nEasiest achievements you haven't unlocked yet:")
        for row in next_easiest(session, STEAM_ID):
            print(f"  {row.global_percent:5.1f}%  {row.display_name:<35} {row.game_name}")

        stats = player_stats(session, STEAM_ID)
        stats.pop("unlocks_by_month")
        print("\nStats:", stats)
