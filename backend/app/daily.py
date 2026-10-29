"""Every once-a-day job, in the right order.

Run it by hand (from the backend folder):  python -m app.daily
In Docker, the scheduler container runs it automatically every day.
"""

import logging

from app.charts import update_charts
from app.snapshots import take_snapshots
from app.sync import configure_cli_logging

logger = logging.getLogger(__name__)


def run_daily():
    """Run every daily job. Safe to run more than once a day: repeats are skipped."""
    # Charts first: new chart games then get included in today's snapshots
    charts = update_charts()
    logger.info("Chart: %s saved, %s failed", charts.get("saved", 0), charts.get("failed", 0))

    snapshots = take_snapshots()
    logger.info(
        "Snapshots: %s saved, %s already done today, %s failed",
        snapshots.get("saved", 0),
        snapshots.get("skipped", 0),
        snapshots.get("failed", 0),
    )


if __name__ == "__main__":
    configure_cli_logging()
    run_daily()
