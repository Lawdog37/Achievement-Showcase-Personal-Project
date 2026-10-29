"""Read-only endpoints: profile, showcase, progress and stats."""

import re
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import delete

from app import queries, steam_client
from app.deps import CurrentPlayer, DbSession, OwnerOnly, SteamId
from app.models import Hunt, Player, PlayerAchievement, PlayerGame
from app.schemas import (
    GameCompletion,
    InProgressOut,
    PlayerOut,
    ResolveOut,
    ShowcaseItem,
    StatsOut,
)

router = APIRouter(prefix="/api", tags=["players"])

STEAM_ID_RE = re.compile(r"^\d{17}$")
PROFILE_URL_RE = re.compile(r"steamcommunity\.com/profiles/(\d{17})")
VANITY_URL_RE = re.compile(r"steamcommunity\.com/id/([^/?#]+)")
VANITY_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{2,32}$")


@router.get("/resolve", response_model=ResolveOut)
def resolve_player(
    q: Annotated[
        str,
        Query(min_length=2, max_length=200, description="SteamID, profile URL or custom name"),
    ],
):
    """Turn whatever the user typed into a SteamID."""
    q = q.strip()
    if STEAM_ID_RE.match(q):
        return {"steam_id": q}
    if match := PROFILE_URL_RE.search(q):
        return {"steam_id": match.group(1)}

    match = VANITY_URL_RE.search(q)
    name = match.group(1) if match else q
    if not VANITY_NAME_RE.match(name):
        raise HTTPException(400, "That doesn't look like a SteamID, profile URL or custom name")
    try:
        steam_id = steam_client.resolve_vanity_url(name)
    except steam_client.SteamAPIError as error:
        raise HTTPException(502, f"Steam request failed: {error}") from None
    if steam_id is None:
        raise HTTPException(404, f"No Steam profile found for '{name}'")
    return {"steam_id": steam_id}


@router.get("/players/{steam_id}", response_model=PlayerOut)
def read_player(player: CurrentPlayer):
    return player


@router.get("/players/{steam_id}/showcase", response_model=list[ShowcaseItem])
def read_showcase(
    player: CurrentPlayer,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
):
    """The player's rarest unlocked achievements."""
    return queries.rarest_unlocked(db, player.steam_id, limit)


@router.get("/players/{steam_id}/in-progress", response_model=InProgressOut)
def read_in_progress(
    player: CurrentPlayer,
    db: DbSession,
    games_limit: Annotated[int, Query(ge=1, le=50)] = 10,
    achievements_limit: Annotated[int, Query(ge=1, le=50)] = 10,
):
    """Games closest to 100%, and the easiest achievements still locked."""
    return {
        "games": queries.games_in_progress(db, player.steam_id, games_limit),
        "next_easiest": queries.next_easiest(db, player.steam_id, achievements_limit),
    }


@router.get("/players/{steam_id}/stats", response_model=StatsOut)
def read_stats(player: CurrentPlayer, db: DbSession):
    return queries.player_stats(db, player.steam_id)


@router.get("/players/{steam_id}/games", response_model=list[GameCompletion])
def read_games(
    player: CurrentPlayer,
    db: DbSession,
    status: Literal["in_progress", "completed", "not_started", "all"] = "in_progress",
    sort: Literal["percent", "remaining", "name", "recent"] = "percent",
):
    """Every game with achievements and its completion, filtered and sorted."""
    return queries.player_games(db, player.steam_id, status, sort)


@router.delete("/players/{steam_id}", status_code=204, dependencies=[OwnerOnly])
def delete_my_data(steam_id: SteamId, db: DbSession, request: Request):
    """Delete everything stored about you, then sign you out.

    Games, achievement lists and rarity snapshots stay: they're about the games,
    not about you. Syncing again later simply starts fresh.
    """
    for model in (Hunt, PlayerAchievement, PlayerGame, Player):  # children before parent
        db.execute(delete(model).where(model.steam_id == steam_id))
    db.commit()
    request.session.clear()
