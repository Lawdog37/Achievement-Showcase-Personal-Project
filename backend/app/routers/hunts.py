"""The Hunting page: games a player has chosen to work on."""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from app import queries
from app.deps import CurrentPlayer, DbSession, OwnerOnly
from app.models import Game, Hunt, PlayerGame
from app.schemas import HuntOut
from app.steam_client import SteamAPIError
from app.sync import SyncError, sync_player

router = APIRouter(prefix="/api/players/{steam_id}/hunts", tags=["hunts"])


@router.get("", response_model=list[HuntOut])
def read_hunts(player: CurrentPlayer, db: DbSession):
    """Every hunted game with its progress and all of its locked achievements."""
    return queries.player_hunts(db, player.steam_id)


@router.put("/{app_id}", status_code=204, dependencies=[OwnerOnly])
def add_hunt(app_id: int, player: CurrentPlayer, db: DbSession):
    """Start hunting a game. Doing it twice is harmless: that's what PUT means."""
    if db.get(PlayerGame, (player.steam_id, app_id)) is None:
        raise HTTPException(404, "This player doesn't own that game")
    if not db.get(Game, app_id).has_achievements:
        raise HTTPException(400, "No achievements found for that game. Play it, then sync.")
    if db.get(Hunt, (player.steam_id, app_id)) is None:
        db.add(Hunt(steam_id=player.steam_id, app_id=app_id, added_at=datetime.now(UTC)))
        db.commit()


@router.delete("/{app_id}", status_code=204, dependencies=[OwnerOnly])
def remove_hunt(app_id: int, player: CurrentPlayer, db: DbSession):
    """Stop hunting a game. Removing one that isn't there is also fine."""
    hunt = db.get(Hunt, (player.steam_id, app_id))
    if hunt is not None:
        db.delete(hunt)
        db.commit()


@router.post("/{app_id}/refresh", status_code=204, dependencies=[OwnerOnly])
def refresh_hunt(app_id: int, player: CurrentPlayer, db: DbSession):
    """Re-sync just this one game from Steam. Takes a second or two."""
    if db.get(Hunt, (player.steam_id, app_id)) is None:
        raise HTTPException(404, "You're not hunting that game")
    try:
        sync_player(player.steam_id, only_app_id=app_id)
    except (SyncError, SteamAPIError) as error:
        raise HTTPException(502, str(error)) from None
