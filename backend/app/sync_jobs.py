"""Keeps track of syncs running in the background.

Status lives in memory, which is fine for one server on your PC. It is wiped
when the server restarts; a hosted version would use a job queue (Phase 8).
"""

import logging
import threading
from datetime import UTC, datetime

from app.sync import SyncError, sync_player

logger = logging.getLogger(__name__)

_jobs: dict[str, dict] = {}
_lock = threading.Lock()  # syncs run in other threads, so guard shared data


def get_status(steam_id):
    with _lock:
        return dict(_jobs.get(steam_id) or {"steam_id": steam_id, "state": "idle"})


def try_start(steam_id):
    """Mark a sync as running. Returns False if one is already running."""
    with _lock:
        if _jobs.get(steam_id, {}).get("state") == "running":
            return False
        _jobs[steam_id] = {
            "steam_id": steam_id,
            "state": "running",
            "started_at": datetime.now(UTC),
        }
        return True


def run(steam_id, force):
    """The actual work. FastAPI runs this in a background thread."""
    try:
        result = sync_player(steam_id, force=force)
        update = {"state": "done", "result": result}
    except SyncError as error:
        update = {"state": "failed", "error": str(error)}
    except Exception:
        logger.exception("Sync crashed for %s", steam_id)
        update = {"state": "failed", "error": "Unexpected error. Check the server logs."}
    update["finished_at"] = datetime.now(UTC)
    with _lock:
        _jobs[steam_id].update(update)
