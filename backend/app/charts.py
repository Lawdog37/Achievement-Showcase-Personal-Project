"""Save Steam's daily "most played" chart, plus each game's achievement rarity.

Run it on its own (from the backend folder):  python -m app.charts
Normally it runs as part of the daily job:     python -m app.daily
"""

import logging
import time
from collections import Counter

from app import steam_client as steam
from app.database import SessionLocal
from app.models import ChartEntry, Game
from app.sync import (
    DELAY_BETWEEN_GAMES,
    configure_cli_logging,
    now_utc,
    percentages_are_stale,
    refresh_percentages,
    save_schema,
)

logger = logging.getLogger(__name__)

CHART_SIZE = 25  # how many of Steam's top 100 to keep


def save_store_details(session, app_id):
    """Make sure the game exists in our database with a real name and banner image."""
    game = session.get(Game, app_id)
    if game is not None and game.capsule_url is not None:
        return game  # already have everything; don't ask the Store again

    details = steam.get_store_details(app_id) or {}
    time.sleep(DELAY_BETWEEN_GAMES)  # the Store API is strict about speed
    if game is None:
        game = Game(app_id=app_id, name=details.get("name") or f"App {app_id}")
        session.add(game)
    game.capsule_url = details.get("capsule_url")
    return game


def update_charts(size=CHART_SIZE):
    """Save today's chart. Running it twice in a day just updates the same rows."""
    today = now_utc().date()
    counts = Counter()

    ranks = steam.get_most_played()[:size]
    with SessionLocal() as session:
        for entry in ranks:
            app_id = entry["appid"]
            try:
                game = save_store_details(session, app_id)
                session.flush()
                if game.has_achievements is None:  # never checked this game before
                    save_schema(session, game)
                if game.has_achievements and percentages_are_stale(game):
                    refresh_percentages(session, game)  # also saves today's snapshot
                session.merge(
                    ChartEntry(
                        taken_on=today,
                        rank=entry["rank"],
                        app_id=app_id,
                        last_week_rank=entry.get("last_week_rank"),
                        peak_players=entry.get("peak_in_game", 0),
                    )
                )
                session.commit()
                counts["saved"] += 1
            except (steam.SteamAPIError, KeyError, ValueError) as error:
                session.rollback()
                counts["failed"] += 1
                logger.warning("Chart game %s: failed (%s)", app_id, error)

    return {"games": len(ranks), **counts}


if __name__ == "__main__":
    configure_cli_logging()
    summary = update_charts()
    print(f"Chart: {summary.get('saved', 0)} saved, {summary.get('failed', 0)} failed")
