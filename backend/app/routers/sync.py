"""Start a sync and check on it."""

import math
from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app import sync_jobs
from app.deps import DbSession, OwnerOnly, SteamId
from app.models import Player
from app.schemas import SyncStatus
from app.sync import as_utc, now_utc

router = APIRouter(prefix="/api/players/{steam_id}/sync", tags=["sync"])

SYNC_COOLDOWN = timedelta(minutes=10)


@router.post("", response_model=SyncStatus, status_code=202, dependencies=[OwnerOnly])
def start_sync(
    steam_id: SteamId, db: DbSession, background_tasks: BackgroundTasks, force: bool = False
):
    """Start syncing your own profile in the background. Answers right away."""
    player = db.get(Player, steam_id)
    last_synced = as_utc(player.last_synced_at) if player else None
    if last_synced and now_utc() - last_synced < SYNC_COOLDOWN:
        wait = SYNC_COOLDOWN - (now_utc() - last_synced)
        minutes = math.ceil(wait.total_seconds() / 60)
        raise HTTPException(429, f"Synced recently. You can sync again in {minutes} min.")

    outcome = sync_jobs.try_start(steam_id)
    if outcome == "already_running":
        raise HTTPException(409, "A sync is already running for this player")
    if outcome == "busy":
        raise HTTPException(503, "The server is busy syncing other players. Try again shortly.")
    background_tasks.add_task(sync_jobs.run, steam_id, force)
    return sync_jobs.get_status(steam_id)


@router.get("", response_model=SyncStatus)
def read_sync_status(steam_id: SteamId):
    """Poll this to see when a sync finishes."""
    return sync_jobs.get_status(steam_id)
