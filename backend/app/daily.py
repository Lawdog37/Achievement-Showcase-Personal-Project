"""Every once-a-day job, in the right order.

Run it once a day (from the backend folder):  python -m app.daily
Phase 11 makes the server run it automatically.
"""

from app.charts import update_charts
from app.snapshots import take_snapshots
from app.sync import configure_cli_logging


def main():
    configure_cli_logging()

    # Charts first: new chart games then get included in today's snapshots
    charts = update_charts()
    print(f"Chart: {charts.get('saved', 0)} saved, {charts.get('failed', 0)} failed")

    snapshots = take_snapshots()
    print(
        f"Snapshots: {snapshots.get('saved', 0)} saved, {snapshots.get('skipped', 0)} already "
        f"done today, {snapshots.get('failed', 0)} failed"
    )


if __name__ == "__main__":
    main()
