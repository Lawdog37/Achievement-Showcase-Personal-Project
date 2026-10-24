"""Database tables, written as Python classes (SQLAlchemy 2.0 style)"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, ForeignKeyConstraint, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "players"

    # Stored as text, Javascript cant handle the full ID
    steam_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str]
    avatar_url: Mapped[str | None]
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Game(Base):
    __tablename__ = "games"

    app_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str]
    icon_url: Mapped[str | None]
    notes: Mapped[str | None]

    # None = never checked, True/False = whether the game has achievements
    has_achievements: Mapped[bool | None]
    # When we last fetched global rarity percentages for this game
    percentages_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Achievement(Base):
    """Every achievement a game has, whether or not anyone unlocked it."""

    __tablename__ = "achievements"

    app_id: Mapped[int] = mapped_column(ForeignKey("games.app_id"), primary_key=True)
    api_name: Mapped[str] = mapped_column(String(200), primary_key=True)
    display_name: Mapped[str]
    description: Mapped[str | None]
    icon_url: Mapped[str | None]
    icon_gray_url: Mapped[str | None]
    hidden: Mapped[bool] = mapped_column(default=False)
    global_percent: Mapped[float | None]  # % of all players who unlocked it


class PlayerGame(Base):
    """Games in your library"""

    __tablename__ = "player_games"

    steam_id: Mapped[str] = mapped_column(ForeignKey("players.steam_id"), primary_key=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("games.app_id"), primary_key=True)
    playtime_minutes: Mapped[int] = mapped_column(default=0)
    last_played_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # When we last fetched this player's achievements for this game
    achievements_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PlayerAchievement(Base):
    """One row per achievement UNLOCKED, No row = still locked."""

    __tablename__ = "player_achievements"

    steam_id: Mapped[str] = mapped_column(ForeignKey("players.steam_id"), primary_key=True)
    app_id: Mapped[int] = mapped_column(primary_key=True)
    api_name: Mapped[str] = mapped_column(String(200), primary_key=True)
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # (app_id, api_name) together point at one row in achievements
    __table_args__ = (
        ForeignKeyConstraint(
            ["app_id", "api_name"],
            ["achievements.app_id", "achievements.api_name"],
        ),
    )


class Hunt(Base):
    """A game the player has chosen to work on"""

    __tablename__ = "hunts"

    steam_id: Mapped[str] = mapped_column(ForeignKey("players.steam_id"), primary_key=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("games.app_id"), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class GameSnapshot(Base):
    """A game's global rarity numbers on one day. Saved daily so we can spot
    trends later, like more and more people finishing a game."""

    __tablename__ = "game_snapshots"

    app_id: Mapped[int] = mapped_column(ForeignKey("games.app_id"), primary_key=True)
    taken_on: Mapped[date] = mapped_column(Date, primary_key=True)
    # % of players with the game's rarest achievement: close to "% who got 100%"
    rarest_percent: Mapped[float]
    average_percent: Mapped[float]
    achievement_count: Mapped[int]
