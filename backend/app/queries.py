"""Questions we ask the database, written with SQLAlchemy.

Try it (from the backend folder):  python -m app.queries
"""

from collections import Counter
from statistics import mean

from sqlalchemy import and_, func, select

from app.config import STEAM_ID
from app.database import SessionLocal
from app.models import Achievement, Game, PlayerAchievement, PlayerGame


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
PCT = func.round(100.0 * UNLOCKED / TOTAL, 1)


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
    stmt = (
        _completion_query(steam_id)
        .having(UNLOCKED > 0)
        .having(UNLOCKED < TOTAL)
        .limit(limit)
    )
    return session.execute(stmt).all()


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