"""Tests for private profiles and for deleting your data."""

import pytest
from sqlalchemy import func, select

from app import sync_jobs
from app.database import SessionLocal
from app.models import Game, Hunt, Player, PlayerAchievement, PlayerGame
from app.steam_client import PrivateAchievementsError, get_player_achievements
from app.sync import SyncError, sync_player
from tests.fake_steam import PLAYER_ID, setup_basic_library

ACHIEVEMENTS = "/ISteamUserStats/GetPlayerAchievements/v1/"


def count(model):
    with SessionLocal() as session:
        return session.scalar(select(func.count()).select_from(model))


# --- "Steam won't tell us" must never look like "no achievements" ---------
def test_private_achievements_raise_instead_of_returning_nothing(steam):
    steam.get(ACHIEVEMENTS).respond(
        403, json={"playerstats": {"error": "Profile is not public", "success": False}}
    )

    with pytest.raises(PrivateAchievementsError, match="Game details"):
        get_player_achievements(PLAYER_ID, 10)


def test_private_achievements_stop_the_sync_and_save_nothing(steam):
    setup_basic_library(steam)
    steam.get(ACHIEVEMENTS, params={"appid": 10}).respond(403)  # Steam refuses

    with pytest.raises(SyncError, match="Game details"):
        sync_player(PLAYER_ID)

    assert count(PlayerAchievement) == 0
    with SessionLocal() as session:
        # Not marked as synced (the game was rolled back), so the next sync tries again
        player_game = session.get(PlayerGame, (PLAYER_ID, 10))
        assert player_game is None or player_game.achievements_synced_at is None
        # And no "last synced" time, so the cooldown doesn't block retrying
        assert session.get(Player, PLAYER_ID).last_synced_at is None


def test_sync_button_shows_the_privacy_message(client, steam, signed_in):
    setup_basic_library(steam)
    steam.get(ACHIEVEMENTS, params={"appid": 10}).respond(403)

    client.post(f"/api/players/{PLAYER_ID}/sync")
    status = client.get(f"/api/players/{PLAYER_ID}/sync").json()

    assert status["state"] == "failed"
    assert "Game details to Public" in status["error"]


def test_full_resync_refetches_games_already_synced(client, steam, signed_in):
    setup_basic_library(steam)
    sync_player(PLAYER_ID)
    with SessionLocal() as session:  # let the cooldown pass
        session.get(Player, PLAYER_ID).last_synced_at = None
        session.commit()

    client.post(f"/api/players/{PLAYER_ID}/sync", params={"force": "true"})

    assert sync_jobs.get_status(PLAYER_ID)["result"]["synced"] == 3  # every game, not 0


# --- Delete my data ------------------------------------------------------
@pytest.fixture
def library_with_a_hunt(client, steam, signed_in):
    setup_basic_library(steam)
    sync_player(PLAYER_ID)
    client.put(f"/api/players/{PLAYER_ID}/hunts/10")


def test_delete_my_data(client, library_with_a_hunt):
    response = client.delete(f"/api/players/{PLAYER_ID}")

    assert response.status_code == 204
    assert client.get(f"/api/players/{PLAYER_ID}").status_code == 404
    assert count(Hunt) == count(PlayerAchievement) == count(PlayerGame) == count(Player) == 0
    assert count(Game) == 3  # facts about games aren't personal data, so they stay


def test_you_cannot_delete_someone_else(client, library_with_a_hunt):
    from app.deps import current_user_id
    from app.main import app

    app.dependency_overrides[current_user_id] = lambda: "76561190000000002"
    assert client.delete(f"/api/players/{PLAYER_ID}").status_code == 403
    assert count(Player) == 1


def test_deleting_needs_sign_in(client):
    assert client.delete(f"/api/players/{PLAYER_ID}").status_code == 401
