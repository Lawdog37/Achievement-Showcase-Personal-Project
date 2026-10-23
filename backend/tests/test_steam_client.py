"""Tests for the Steam API wrapper (app/steam_client.py)."""

import httpx
import pytest

from app import steam_client
from app.steam_client import SteamAPIError

PATH = "/ISteamUser/GetPlayerSummaries/v2/"


def test_retries_when_steam_says_slow_down(steam):
    route = steam.get(PATH)
    route.side_effect = [
        httpx.Response(429),  # "too many requests"
        httpx.Response(200, json={"response": {"players": []}}),
    ]

    assert steam_client.get_player_summary("1") is None
    assert route.call_count == 2


def test_gives_up_after_max_attempts(steam):
    route = steam.get(PATH).respond(503)

    with pytest.raises(SteamAPIError):
        steam_client.get_player_summary("1")
    assert route.call_count == steam_client.MAX_ATTEMPTS


def test_error_messages_never_contain_the_api_key(steam):
    steam.get(PATH).respond(403)

    with pytest.raises(SteamAPIError) as caught:
        steam_client.get_player_summary("1")
    assert "fake-test-key" not in str(caught.value)
    assert caught.value.status_code == 403


def test_game_without_stats_means_no_achievements(steam):
    steam.get("/ISteamUserStats/GetPlayerAchievements/v1/").respond(400)

    assert steam_client.get_player_achievements("1", 99) == []


def test_steam_outage_is_not_mistaken_for_no_achievements(steam):
    steam.get("/ISteamUserStats/GetPlayerAchievements/v1/").respond(503)

    with pytest.raises(SteamAPIError):
        steam_client.get_player_achievements("1", 99)
