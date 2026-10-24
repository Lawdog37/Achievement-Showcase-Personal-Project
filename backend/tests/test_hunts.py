"""Tests for the Hunting page endpoints (app/routers/hunts.py)."""

import pytest

from app.sync import sync_player
from tests.fake_steam import PLAYER_ID, setup_basic_library

HUNTS = f"/api/players/{PLAYER_ID}/hunts"


@pytest.fixture
def library(steam):
    """Game 10 has 3 achievements (2 unlocked), game 20 has none, 30 is unplayed."""
    setup_basic_library(steam)
    sync_player(PLAYER_ID)


def test_starts_empty(client, library):
    assert client.get(HUNTS).json() == []


def test_add_a_hunt_and_see_what_is_left(client, library):
    assert client.put(f"{HUNTS}/10").status_code == 204

    hunts = client.get(HUNTS).json()
    assert len(hunts) == 1
    assert hunts[0]["game"]["name"] == "Rare Game"
    assert hunts[0]["game"]["remaining"] == 1
    assert [a["api_name"] for a in hunts[0]["locked"]] == ["TUTORIAL"]


def test_adding_twice_is_harmless(client, library):
    client.put(f"{HUNTS}/10")
    client.put(f"{HUNTS}/10")
    assert len(client.get(HUNTS).json()) == 1


def test_cannot_hunt_a_game_without_achievements(client, library):
    assert client.put(f"{HUNTS}/20").status_code == 400


def test_cannot_hunt_a_game_you_do_not_own(client, library):
    assert client.put(f"{HUNTS}/999").status_code == 404


def test_remove_a_hunt(client, library):
    client.put(f"{HUNTS}/10")
    assert client.delete(f"{HUNTS}/10").status_code == 204
    assert client.get(HUNTS).json() == []
    assert client.delete(f"{HUNTS}/10").status_code == 204  # removing again is fine


def test_refresh_resyncs_the_game(client, library, steam):
    client.put(f"{HUNTS}/10")
    calls_before = len(steam.calls)

    assert client.post(f"{HUNTS}/10/refresh").status_code == 204
    assert len(steam.calls) > calls_before  # it really asked Steam again


def test_refresh_needs_the_game_to_be_hunted(client, library):
    assert client.post(f"{HUNTS}/10/refresh").status_code == 404


def test_unknown_player(client):
    assert client.get("/api/players/76561190000000099/hunts").status_code == 404
