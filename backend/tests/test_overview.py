"""Tests for the Overview page: the chart job, trending, and GET /api/overview."""

from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.charts import update_charts
from app.database import SessionLocal
from app.models import ChartEntry, Game, GameSnapshot
from app.sync import now_utc
from tests.fake_steam import add_game_achievements, add_game_without_achievements

STORE_URL = "https://store.steampowered.com/api/appdetails"


def add_chart(steam, app_ids):
    """Steam's most-played chart, in the order given."""
    steam.get("/ISteamChartsService/GetMostPlayedGames/v1/").respond(
        json={
            "response": {
                "ranks": [
                    {"rank": i, "appid": app_id, "last_week_rank": i + 1, "peak_in_game": 1000 - i}
                    for i, app_id in enumerate(app_ids, start=1)
                ]
            }
        }
    )


def add_store_page(steam, app_id, name):
    return steam.get(STORE_URL, params={"appids": app_id}).respond(
        json={
            str(app_id): {
                "success": True,
                "data": {"name": name, "capsule_image": f"https://example.com/{app_id}.jpg"},
            }
        }
    )


@pytest.fixture
def chart(steam):
    """Three popular games: one with achievements, one without, one the Store can't find."""
    add_chart(steam, [10, 20, 30])
    add_store_page(steam, 10, "Popular Game")
    add_store_page(steam, 20, "Achievement-Free Game")
    steam.get(STORE_URL, params={"appids": 30}).respond(500)  # the Store is having a bad day
    add_game_achievements(steam, 10, [("EASY", 80.0, False), ("HARD", 0.7, False)])
    add_game_without_achievements(steam, 20)
    add_game_without_achievements(steam, 30)
    return steam


def test_overview_is_empty_before_any_data(client):
    data = client.get("/api/overview").json()
    assert data == {"chart_date": None, "most_played": [], "trending": [], "snapshot_days": 0}


def test_chart_job_saves_the_chart(chart):
    summary = update_charts()

    assert summary["saved"] == 3
    with SessionLocal() as session:
        assert session.get(Game, 10).name == "Popular Game"
        assert session.get(Game, 30).name == "App 30"  # Store failed, so a fallback name


def test_overview_lists_most_played_with_difficulty(client, chart):
    update_charts()

    games = client.get("/api/overview").json()["most_played"]

    assert [g["name"] for g in games] == ["Popular Game", "Achievement-Free Game", "App 30"]
    assert games[0]["rarest_percent"] == pytest.approx(0.7)  # the HARD achievement
    assert games[0]["achievement_count"] == 2
    assert games[0]["image_url"] == "https://example.com/10.jpg"
    assert games[1]["has_achievements"] is False
    assert games[1]["rarest_percent"] is None


def test_running_twice_a_day_does_not_duplicate(chart):
    update_charts()
    store_calls = len([c for c in chart.calls if "store.steampowered.com" in str(c.request.url)])

    update_charts()

    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(ChartEntry)) == 3
    store_calls_after = len(
        [c for c in chart.calls if "store.steampowered.com" in str(c.request.url)]
    )
    # Only the game with no banner yet (the one the Store failed on) is looked up again
    assert store_calls_after == store_calls + 1


# --- Trending: built from snapshots we insert by hand --------------------
def add_snapshots(app_id, name, rarest_by_days_ago):
    """rarest_by_days_ago: {days ago: rarest_percent}"""
    today = now_utc().date()
    with SessionLocal() as session:
        session.add(Game(app_id=app_id, name=name, has_achievements=True))
        for days_ago, rarest in rarest_by_days_ago.items():
            session.add(
                GameSnapshot(
                    app_id=app_id,
                    taken_on=today - timedelta(days=days_ago),
                    rarest_percent=rarest,
                    average_percent=20.0,
                    achievement_count=10,
                )
            )
        session.commit()


def test_trending_lists_games_people_are_finishing(client):
    add_snapshots(1, "Fast Riser", {6: 1.0, 3: 1.4, 0: 2.0})  # +1.0 points
    add_snapshots(2, "Slow Riser", {5: 3.0, 0: 3.2})  # +0.2
    add_snapshots(3, "Falling", {5: 4.0, 0: 3.5})  # going down: not trending
    add_snapshots(4, "Too New", {0: 9.0})  # only one day: can't tell yet
    add_snapshots(5, "Too Old", {30: 1.0, 20: 5.0})  # outside the last 7 days

    data = client.get("/api/overview").json()

    assert [g["name"] for g in data["trending"]] == ["Fast Riser", "Slow Riser"]
    fast = data["trending"][0]
    assert fast["rarest_before"] == 1.0
    assert fast["rarest_now"] == 2.0
    assert fast["change"] == pytest.approx(1.0)
    assert fast["days"] == 6
    assert data["snapshot_days"] == 6  # distinct days: 0, 3, 5, 6, 20 and 30 days ago
