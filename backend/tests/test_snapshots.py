"""Tests for the daily rarity snapshots (app/snapshots.py and the sync)."""

import pytest
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import GameSnapshot
from app.snapshots import take_snapshots
from app.sync import now_utc, sync_player
from tests.fake_steam import PLAYER_ID, setup_basic_library


def snapshot_count():
    with SessionLocal() as session:
        return session.scalar(select(func.count()).select_from(GameSnapshot))


def percentage_requests(steam):
    """How many times the fake Steam was asked for global percentages."""
    return sum("GetGlobalAchievementPercentages" in str(call.request.url) for call in steam.calls)


def test_sync_saves_a_snapshot(steam):
    setup_basic_library(steam)
    sync_player(PLAYER_ID)

    with SessionLocal() as session:
        snapshot = session.get(GameSnapshot, (10, now_utc().date()))
    assert snapshot.rarest_percent == pytest.approx(0.4)  # LEGEND
    assert snapshot.average_percent == pytest.approx((0.4 + 12.5 + 91.0) / 3, abs=0.01)
    assert snapshot.achievement_count == 3


def test_daily_job_skips_games_already_done_today(steam):
    setup_basic_library(steam)
    sync_player(PLAYER_ID)  # this already saved today's snapshot for game 10
    requests_before = percentage_requests(steam)

    summary = take_snapshots()

    assert summary["skipped"] == 1
    assert percentage_requests(steam) == requests_before  # Steam wasn't asked again
    assert snapshot_count() == 1


def test_force_takes_them_again_without_duplicates(steam):
    setup_basic_library(steam)
    sync_player(PLAYER_ID)

    summary = take_snapshots(force=True)

    assert summary["saved"] == 1
    assert snapshot_count() == 1  # same game, same day: updated, not duplicated
