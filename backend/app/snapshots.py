"""Save a daily snapshot of every game's global rarity.

Steam only tells us today's numbers, never history. Saving them once a day
builds our own history, which Phase 10 uses to spot trending games.

Run it once a day (from the backend folder):  python -m app.snapshots
"""

import argparse
import logging
import time
from collections import Counter

from sqlalchemy import select

from app import steam_client as steam
from app.database import SessionLocal
from app.models import Game, GameSnapshot
from app.sync import DELAY_BETWEEN_GAMES, configure_cli_logging, now_utc, refresh_percentages

logger = logging.getLogger(__name__)


def take_snapshots(force=False):
    """Refresh rarity and save a snapshot for every game with achievements.
    Games that already have today's snapshot are skipped unless force=True."""
    counts = Counter()
    today = now_utc().date()

    with SessionLocal() as session:
        games = session.scalars(
            select(Game).where(Game.has_achievements.is_(True)).order_by(Game.name)
        ).all()

        for game in games:
            if not force and session.get(GameSnapshot, (game.app_id, today)):
                counts["skipped"] += 1
                continue
            try:
                refresh_percentages(session, game)
                session.commit()
                counts["saved"] += 1
                time.sleep(DELAY_BETWEEN_GAMES)
            except (steam.SteamAPIError, KeyError, ValueError) as error:
                session.rollback()
                counts["failed"] += 1
                logger.warning("%s: failed (%s)", game.name, error)

    return {"games": len(games), **counts}


def main():
    parser = argparse.ArgumentParser(description="Save today's rarity snapshot for every game.")
    parser.add_argument("--force", action="store_true", help="redo games already saved today")
    args = parser.parse_args()
    configure_cli_logging()

    summary = take_snapshots(force=args.force)
    print(
        f"Snapshots: {summary.get('saved', 0)} saved, {summary.get('skipped', 0)} already "
        f"done today, {summary.get('failed', 0)} failed (out of {summary['games']} games)"
    )


if __name__ == "__main__":
    main()
