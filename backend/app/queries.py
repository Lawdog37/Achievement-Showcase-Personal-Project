"""Questions we ask the database, written with SQLAlchemy.

Try it (from the backend folder):  python -m app.queries
"""

from sqlalchemy import and_, func, select

from app.config import STEAM_ID
from app.database import SessionLocal
from app.models import Achievement, Game, PlayerAchievement, PlayerGame


def rarest_unlocked(session, steam_id, limit=10):
    """Your unlocked achievements, rarest first."""
    stmt = (
        select(
            Game.name,
            Achievement.display_name,
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
        .order_by(Achievement.global_percent)
        .limit(limit)
    )
    return session.execute(stmt).all()


def completion_by_game(session, steam_id):
    """How many achievements you have in each game, and the percentage."""
    total = func.count(Achievement.api_name)
    unlocked = func.count(PlayerAchievement.api_name)
    pct = func.round(100.0 * unlocked / total, 1)

    stmt = (
        select(
            Game.name,
            total.label("total"),
            unlocked.label("unlocked"),
            pct.label("pct"),
        )
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
        .group_by(Game.app_id, Game.name)
        .order_by(pct.desc())
    )
    return session.execute(stmt).all()


def next_easiest(session, steam_id, limit=5):
    """Locked achievements that the most players have, so the easiest to get next."""
    stmt = (
        select(Game.name, Achievement.display_name, Achievement.global_percent)
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
        .where(PlayerAchievement.api_name.is_(None))  # no unlock row = locked
        .order_by(Achievement.global_percent.desc())
        .limit(limit)
    )
    return session.execute(stmt).all()


if __name__ == "__main__":
    with SessionLocal() as session:
        print("Your rarest achievements across all loaded games:")
        for row in rarest_unlocked(session, STEAM_ID):
            print(f"  {row.global_percent:5.1f}%  {row.display_name:<35} {row.name}")

        print("\nCompletion by game:")
        for row in completion_by_game(session, STEAM_ID):
            print(f"  {row.pct:5.1f}%  {row.unlocked:>4}/{row.total:<4} {row.name}")

        print("\nEasiest achievements you haven't unlocked yet:")
        for row in next_easiest(session, STEAM_ID):
            print(f"  {row.global_percent:5.1f}%  {row.display_name:<35} {row.name}")