"""Tests for the scheduler's timing (app/scheduler.py)."""

from datetime import UTC, datetime

from app import scheduler
from app.scheduler import seconds_until_next_run

HOUR = 3600


def at(hour, minute=0):
    return datetime(2026, 10, 24, hour, minute, tzinfo=UTC)


def test_waits_until_later_today():
    assert seconds_until_next_run(at(4), hour=6) == 2 * HOUR


def test_waits_until_tomorrow_once_today_has_passed():
    assert seconds_until_next_run(at(7), hour=6) == 23 * HOUR


def test_exactly_on_time_means_tomorrow_not_right_now():
    assert seconds_until_next_run(at(6), hour=6) == 24 * HOUR


def test_a_failed_run_does_not_crash_the_scheduler(monkeypatch):
    def broken_daily_job():
        raise RuntimeError("Steam is down")

    monkeypatch.setattr(scheduler, "run_daily", broken_daily_job)
    scheduler.run_safely()  # must not raise
