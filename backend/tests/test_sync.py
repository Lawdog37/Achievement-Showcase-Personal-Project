"""Tests for the sync service (app/sync.py)."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import Achievement, Game, PlayerAchievement, PlayerGame
from app.sync import SyncError, needs_sync, sync_player
from tests.fake_steam import PLAYER_ID, add_owned_games, add_profile, setup_basic_library


def count(model):
    with SessionLocal() as session:
        return session.scalar(select(func.count()).select_from(model))


def test_first_sync_saves_everything(steam):
    setup_basic_library(steam)

    summary = sync_player(PLAYER_ID)

    assert summary["synced"] == 2  # the two played games
    assert summary["skipped"] == 1  # the never-played game
    assert summary["failed"] == 0
    assert count(Game) == 3
    assert count(PlayerGame) == 3
    assert count(Achievement) == 3
    assert count(PlayerAchievement) == 2  # LEGEND and VETERAN, not TUTORIAL


def test_percentages_are_saved_as_numbers(steam):
    setup_basic_library(steam)
    sync_player(PLAYER_ID)

    with SessionLocal() as session:
        legend = session.get(Achievement, (10, "LEGEND"))
    assert legend.global_percent == pytest.approx(0.4)


def test_game_without_achievements_is_remembered(steam):
    setup_basic_library(steam)
    sync_player(PLAYER_ID)

    with SessionLocal() as session:
        assert session.get(Game, 20).has_achievements is False
        assert session.get(Game, 10).has_achievements is True


def test_second_sync_skips_unchanged_games(steam):
    setup_basic_library(steam)
    sync_player(PLAYER_ID)

    summary = sync_player(PLAYER_ID)

    assert summary["synced"] == 0
    assert summary["skipped"] == 3


def test_running_twice_does_not_duplicate_rows(steam):
    setup_basic_library(steam)
    sync_player(PLAYER_ID, force=True)
    sync_player(PLAYER_ID, force=True)

    assert count(Achievement) == 3
    assert count(PlayerAchievement) == 2


def test_private_profile_stops_the_sync(steam):
    add_profile(steam, visibility=1)

    with pytest.raises(SyncError, match="private"):
        sync_player(PLAYER_ID)


def test_hidden_game_details_stop_the_sync(steam):
    add_profile(steam)
    add_owned_games(steam, [])

    with pytest.raises(SyncError, match="Game details"):
        sync_player(PLAYER_ID)


def test_one_broken_game_does_not_stop_the_others(steam):
    setup_basic_library(steam)
    # Steam keeps failing for game 20's schema, even after retries
    steam.get("/ISteamUserStats/GetSchemaForGame/v2/", params={"appid": 20}).respond(503)

    summary = sync_player(PLAYER_ID)

    assert summary["failed"] == 1
    assert summary["synced"] == 1
    assert count(PlayerAchievement) == 2  # game 10 was still saved


# --- needs_sync on its own: no database or Steam needed ------------------
NOW = datetime(2026, 1, 1, tzinfo=UTC)


def make_rows(has_achievements=True, synced_at=None, last_played=None):
    game = Game(app_id=1, name="Game", has_achievements=has_achievements)
    player_game = PlayerGame(
        steam_id=PLAYER_ID,
        app_id=1,
        achievements_synced_at=synced_at,
        last_played_at=last_played,
    )
    return game, player_game


@pytest.mark.parametrize(
    ("description", "rows", "playtime", "force", "expected"),
    [
        ("never synced", make_rows(), 60, False, True),
        ("never played", make_rows(), 0, False, False),
        ("known to have no achievements", make_rows(has_achievements=False), 60, False, False),
        (
            "played since last sync",
            make_rows(synced_at=NOW - timedelta(days=2), last_played=NOW - timedelta(days=1)),
            60,
            False,
            True,
        ),
        (
            "not played since last sync",
            make_rows(synced_at=NOW - timedelta(days=1), last_played=NOW - timedelta(days=2)),
            60,
            False,
            False,
        ),
        ("force always syncs", make_rows(has_achievements=False), 0, True, True),
    ],
)
def test_needs_sync(description, rows, playtime, force, expected):
    game, player_game = rows
    assert needs_sync(game, player_game, playtime, force) is expected, description
