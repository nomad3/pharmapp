"""Scheduled tasks for automated scraping and maintenance."""
import logging

logger = logging.getLogger(__name__)


async def run_scheduled_scrape():
    """Run daily catalog scrape for all chains. Called by APScheduler."""
    from app.tasks.scraping import run_catalog_scrape_with_session

    logger.info("Starting scheduled catalog scrape...")
    try:
        result = await run_catalog_scrape_with_session(chains=None)
        logger.info("Scheduled scrape completed: %s", result)
    except Exception:
        logger.exception("Scheduled scrape failed")
