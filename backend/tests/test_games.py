"""Tests for GET /api/players/{steam_id}/games (the Near completion page)."""

import pytest

from app.sync import sync_player
from tests.fake_steam import (
    NOW,
    PLAYER_ID,
    add_game_achievements,
    add_owned_games,
    add_profile,
)


@pytest.fixture
def library(steam):
    """Four games, one in each state the page cares about."""
    add_profile(steam)
    add_owned_games(
        steam,
        [
            (10, "Almost Done", 600, NOW - 100),  # 2 of 3 unlocked
            (20, "Finished", 300, NOW - 300),  # 2 of 2
            (30, "Barely Started", 60, NOW - 200),  # 1 of 4
            (40, "Untouched", 30, NOW - 400),  # 0 of 2
        ],
    )
    add_game_achievements(steam, 10, [("A", 50, True), ("B", 40, True), ("C", 5, False)])
    add_game_achievements(steam, 20, [("A", 60, True), ("B", 30, True)])
    add_game_achievements(
        steam, 30, [("A", 70, True), ("B", 20, False), ("C", 10, False), ("D", 2, False)]
    )
    add_game_achievements(steam, 40, [("A", 80, False), ("B", 40, False)])
    sync_player(PLAYER_ID)


def names(client, **params):
    response = client.get(f"/api/players/{PLAYER_ID}/games", params=params)
    assert response.status_code == 200
    return [game["name"] for game in response.json()]


def test_default_is_in_progress_closest_to_done_first(client, library):
    assert names(client) == ["Almost Done", "Barely Started"]


def test_completed(client, library):
    assert names(client, status="completed") == ["Finished"]


def test_not_started(client, library):
    assert names(client, status="not_started") == ["Untouched"]


def test_all_games(client, library):
    assert len(names(client, status="all")) == 4


def test_sort_by_fewest_remaining(client, library):
    assert names(client, status="all", sort="remaining") == [
        "Finished",  # 0 left
        "Almost Done",  # 1 left
        "Untouched",  # 2 left
        "Barely Started",  # 3 left
    ]


def test_sort_by_recently_played(client, library):
    assert names(client, status="all", sort="recent") == [
        "Almost Done",
        "Barely Started",
        "Finished",
        "Untouched",
    ]


def test_each_game_has_its_numbers(client, library):
    games = client.get(f"/api/players/{PLAYER_ID}/games").json()
    almost_done = games[0]
    assert almost_done["unlocked"] == 2
    assert almost_done["total"] == 3
    assert almost_done["remaining"] == 1
    assert almost_done["pct"] == pytest.approx(66.7)
    assert almost_done["playtime_minutes"] == 600


def test_unknown_status_is_rejected(client, library):
    response = client.get(f"/api/players/{PLAYER_ID}/games", params={"status": "nope"})
    assert response.status_code == 422
