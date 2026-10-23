"""Tests for the web API (app/main.py and app/routers/)."""

from app.sync import sync_player
from tests.fake_steam import PLAYER_ID, setup_basic_library


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_player_is_404(client):
    response = client.get(f"/api/players/{PLAYER_ID}")
    assert response.status_code == 404


def test_invalid_steam_id_is_rejected(client):
    response = client.get("/api/players/not-a-number")
    assert response.status_code == 422


def test_showcase_is_rarest_first(client, steam):
    setup_basic_library(steam)
    sync_player(PLAYER_ID)

    response = client.get(f"/api/players/{PLAYER_ID}/showcase")

    assert response.status_code == 200
    names = [item["api_name"] for item in response.json()]
    assert names == ["LEGEND", "VETERAN"]  # 0.4% before 12.5%; TUTORIAL is locked


def test_times_are_sent_in_utc(client, steam):
    setup_basic_library(steam)
    sync_player(PLAYER_ID)

    item = client.get(f"/api/players/{PLAYER_ID}/showcase").json()[0]

    assert item["unlocked_at"].endswith(("Z", "+00:00"))


def test_in_progress_lists_the_easiest_locked_achievement(client, steam):
    setup_basic_library(steam)
    sync_player(PLAYER_ID)

    data = client.get(f"/api/players/{PLAYER_ID}/in-progress").json()

    assert [g["name"] for g in data["games"]] == ["Rare Game"]
    assert data["games"][0]["unlocked"] == 2
    assert data["games"][0]["total"] == 3
    assert [a["api_name"] for a in data["next_easiest"]] == ["TUTORIAL"]


def test_stats(client, steam):
    setup_basic_library(steam)
    sync_player(PLAYER_ID)

    stats = client.get(f"/api/players/{PLAYER_ID}/stats").json()

    assert stats["games_owned"] == 3
    assert stats["achievements_unlocked"] == 2
    assert stats["achievements_total"] == 3
    assert stats["perfect_games"] == 0
    assert stats["hours_played"] == 12.0  # 600 + 120 + 0 minutes


def test_resolve_accepts_a_plain_steam_id_without_calling_steam(client, steam):
    response = client.get("/api/resolve", params={"q": PLAYER_ID})

    assert response.json() == {"steam_id": PLAYER_ID}
    assert not steam.calls  # no request reached the fake Steam


def test_resolve_custom_profile_url(client, steam):
    steam.get("/ISteamUser/ResolveVanityURL/v1/", params={"vanityurl": "tester"}).respond(
        json={"response": {"steamid": PLAYER_ID, "success": 1}}
    )

    response = client.get("/api/resolve", params={"q": "https://steamcommunity.com/id/tester/"})

    assert response.json() == {"steam_id": PLAYER_ID}


def test_sync_endpoint_runs_in_background(client, steam):
    setup_basic_library(steam)

    started = client.post(f"/api/players/{PLAYER_ID}/sync")
    assert started.status_code == 202
    assert started.json()["state"] == "running"

    # TestClient finishes background tasks before returning, so it's done now
    status = client.get(f"/api/players/{PLAYER_ID}/sync").json()
    assert status["state"] == "done"
    assert status["result"]["synced"] == 2
