"""Start a sync and check on it."""

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app import sync_jobs
from app.deps import SteamId
from app.schemas import SyncStatus

router = APIRouter(prefix="/api/players/{steam_id}/sync", tags=["sync"])


@router.post("", response_model=SyncStatus, status_code=202)
def start_sync(steam_id: SteamId, background_tasks: BackgroundTasks, force: bool = False):
    """Start syncing in the background. Answers right away with status 'running'."""
    if not sync_jobs.try_start(steam_id):
        raise HTTPException(409, "A sync is already running for this player")
    background_tasks.add_task(sync_jobs.run, steam_id, force)
    return sync_jobs.get_status(steam_id)


@router.get("", response_model=SyncStatus)
def read_sync_status(steam_id: SteamId):
    """Poll this to see when a sync finishes."""
    return sync_jobs.get_status(steam_id)
