"""The Overview home page: what's popular on Steam and what's trending."""

from fastapi import APIRouter

from app import queries
from app.deps import DbSession
from app.schemas import OverviewOut

router = APIRouter(prefix="/api", tags=["overview"])


@router.get("/overview", response_model=OverviewOut)
def read_overview(db: DbSession):
    """Everything the home page needs, in one request."""
    chart_date, most_played = queries.most_played(db)
    return {
        "chart_date": chart_date,
        "most_played": most_played,
        "trending": queries.trending_games(db),
        "snapshot_days": queries.snapshot_days(db),
    }
