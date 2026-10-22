"""Dependencies: small functions FastAPI runs for you before an endpoint."""

from typing import Annotated

from fastapi import Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Player


def get_db():
    """One database session per request, closed automatically afterwards."""
    with SessionLocal() as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]

SteamId = Annotated[
    str,
    Path(
        pattern = r"^\d{17}$",
        description = "64-bit SteamID (17 digits)",
        examples = ["76561197960287930"],
    ),
]


def get_player(steam_id: SteamId, db: DbSession) -> Player:
    """Look the player up, or stop the request with a 404."""
    player = db.get(Player, steam_id)
    if player is None:
        raise HTTPException(
            status_code = 404,
            detail = "Player not found. Sync them first with POST /api/players/{steam_id}/sync",
        )
    return player


CurrentPlayer = Annotated[Player, Depends(get_player)]