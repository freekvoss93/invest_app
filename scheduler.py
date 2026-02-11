import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

import config
import database
import degiro_client

logger = logging.getLogger(__name__)


def fetch_and_store():
    """Fetch portfolio from DeGiro and store snapshot in the database."""
    try:
        logger.info("Starting portfolio fetch...")
        data = degiro_client.fetch_portfolio()
        snapshot_id = database.insert_snapshot(data["summary"], data["positions"])
        logger.info("Snapshot #%d saved with %d positions", snapshot_id, len(data["positions"]))
    except Exception:
        logger.error("Failed to fetch/store portfolio", exc_info=True)


def start_scheduler():
    """Start the daily scheduler."""
    scheduler = BlockingScheduler()
    trigger = CronTrigger(hour=config.SCHEDULE_HOUR, minute=config.SCHEDULE_MINUTE)
    scheduler.add_job(fetch_and_store, trigger, id="daily_portfolio_fetch")

    logger.info(
        "Scheduler started — will fetch daily at %02d:%02d",
        config.SCHEDULE_HOUR,
        config.SCHEDULE_MINUTE,
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")
