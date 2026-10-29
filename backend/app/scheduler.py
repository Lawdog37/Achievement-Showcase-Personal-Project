"""Runs the daily job once a day, forever. Docker starts this as its own container.

It runs once straight away (so a fresh server has data immediately), then every
day at RUN_AT_HOUR_UTC. Running twice in a day is harmless: the daily job skips
anything it already did today.

Run it by hand (from the backend folder):  python -m app.scheduler
"""

import logging
import os
import time
from datetime import datetime, timedelta

from app.daily import run_daily
from app.sync import configure_cli_logging, now_utc

logger = logging.getLogger(__name__)

# 06:00 UTC is overnight in the Americas: a quiet time for Steam and for us
RUN_AT_HOUR_UTC = int(os.getenv("DAILY_JOB_HOUR_UTC", "6"))


def seconds_until_next_run(now: datetime, hour: int = RUN_AT_HOUR_UTC) -> float:
    """How long to sleep until the next time the clock reaches `hour`:00 UTC."""
    next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(days=1)  # already past today's time: wait for tomorrow
    return (next_run - now).total_seconds()


def run_safely():
    """One failed run (Steam down, say) must not stop tomorrow's run."""
    try:
        run_daily()
    except Exception:
        logger.exception("Daily job failed; will try again at the next scheduled time")


def main():
    configure_cli_logging()
    logger.info("Scheduler started; running the daily job now")
    run_safely()
    while True:
        wait = seconds_until_next_run(now_utc())
        logger.info("Next daily job in %.1f hours", wait / 3600)
        time.sleep(wait)
        run_safely()


if __name__ == "__main__":
    main()
