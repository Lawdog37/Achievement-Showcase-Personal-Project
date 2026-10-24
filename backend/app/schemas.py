"""The shapes of the JSON the API sends back (Pydantic models).

These are separate from models.py on purpose: database tables can change
without breaking the API, and the API never leaks columns by accident.
"""

from datetime import UTC, date, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict


def _assume_utc(value):
    # SQLite gives times back without a time zone. We always store UTC, so say so,
    # or browsers would treat them as local time.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


UtcDatetime = Annotated[datetime, AfterValidator(_assume_utc)]


class Schema(BaseModel):
    # Lets Pydantic read database rows (row.name) as well as dicts (row["name"])
    model_config = ConfigDict(from_attributes=True)


class PlayerOut(Schema):
    steam_id: str
    name: str
    avatar_url: str | None
    last_synced_at: UtcDatetime | None


class ShowcaseItem(Schema):
    app_id: int
    game_name: str
    api_name: str
    display_name: str
    description: str | None
    icon_url: str | None
    global_percent: float
    unlocked_at: UtcDatetime | None


class GameProgress(Schema):
    app_id: int
    name: str
    icon_url: str | None
    unlocked: int
    total: int
    pct: float


class GameCompletion(GameProgress):
    """GameProgress plus a few extra fields (inherits everything above)."""

    remaining: int
    playtime_minutes: int
    last_played_at: UtcDatetime | None


class HuntAchievement(Schema):
    api_name: str
    display_name: str
    description: str | None
    icon_gray_url: str | None
    hidden: bool
    global_percent: float | None


class HuntOut(Schema):
    game: GameCompletion
    added_at: UtcDatetime
    locked: list[HuntAchievement]  # easiest first


class LockedAchievement(Schema):
    app_id: int
    game_name: str
    api_name: str
    display_name: str
    description: str | None
    icon_gray_url: str | None
    global_percent: float


class InProgressOut(Schema):
    games: list[GameProgress]
    next_easiest: list[LockedAchievement]


class MonthCount(Schema):
    month: str  # "2024-06"
    count: int


class StatsOut(Schema):
    games_owned: int
    games_with_achievements: int
    games_started: int
    perfect_games: int
    achievements_unlocked: int
    achievements_total: int
    average_completion: float
    hours_played: float
    unlocks_by_month: list[MonthCount]


class SyncResult(Schema):
    games: int
    synced: int
    skipped: int
    failed: int
    seconds: float


class SyncStatus(Schema):
    steam_id: str
    state: Literal["idle", "running", "done", "failed"]
    started_at: UtcDatetime | None = None
    finished_at: UtcDatetime | None = None
    result: SyncResult | None = None
    error: str | None = None


class ResolveOut(Schema):
    steam_id: str


class ChartGame(Schema):
    rank: int
    last_week_rank: int | None
    peak_players: int
    app_id: int
    name: str
    image_url: str | None
    has_achievements: bool | None
    rarest_percent: float | None  # None until we have a snapshot
    achievement_count: int | None


class TrendingGame(Schema):
    app_id: int
    name: str
    image_url: str | None
    rarest_before: float
    rarest_now: float
    change: float
    days: int


class OverviewOut(Schema):
    chart_date: date | None
    most_played: list[ChartGame]
    trending: list[TrendingGame]
    snapshot_days: int


class MeOut(Schema):
    steam_id: str
