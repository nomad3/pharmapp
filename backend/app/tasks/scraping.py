"""Pharmacy chain price scraping orchestration."""
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.scrapers.drsimi import DrSimiScraper
from app.scrapers.cruzverde import CruzVerdeScraper
from app.scrapers.salcobrand import SalcobrandScraper
from app.scrapers.ahumada import AhumadaScraper
from app.scrapers.query_builder import build_search_queries
from app.etl.scrape_to_marketplace import upsert_scraped_products
from app.models.scrape_run import ScrapeRun

logger = logging.getLogger(__name__)

SCRAPERS = {
    "dr_simi": DrSimiScraper,
    "cruz_verde": CruzVerdeScraper,
    "salcobrand": SalcobrandScraper,
    "ahumada": AhumadaScraper,
}


async def run_scrape_with_session(chains: list[str] | None = None, query_limit: int = 200):
    """Entry point for background tasks — creates its own DB session."""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        return await run_scrape(db, chains, query_limit)
    finally:
        db.close()


async def run_scrape(db: Session, chains: list[str] | None = None, query_limit: int = 200):
    """Run price scraping for specified chains (or all).

    1. Build search queries from existing medications
    2. For each chain, search and collect products
    3. Normalize and upsert into marketplace tables
    4. Record ScrapeRun for monitoring
    """
    chains = chains or list(SCRAPERS.keys())
    queries = build_search_queries(db, limit=query_limit)

    run = ScrapeRun(
        chain=",".join(chains),
        status="running",
        queries_total=len(queries) * len(chains),
    )
    db.add(run)
    db.commit()

    total_products = []
    total_errors = []

    try:
        for chain in chains:
            if chain not in SCRAPERS:
                logger.warning("Unknown chain: %s", chain)
                continue

            scraper = SCRAPERS[chain]()
            logger.info("Scraping %s with %d queries...", chain, len(queries))

            products = await scraper.search_batch(queries)
            total_products.extend(products)
            total_errors.extend(scraper.errors)

            run.queries_completed += len(queries)
            run.products_found += len(products)
            db.commit()

        # ETL: normalize into marketplace
        logger.info("Upserting %d products into marketplace...", len(total_products))
        stats = upsert_scraped_products(db, total_products)

        run.status = "completed"
        run.prices_upserted = stats["prices_upserted"]
        run.medications_created = stats["medications_created"]
        run.pharmacies_created = stats["pharmacies_created"]
        run.errors = total_errors[:100]
        run.finished_at = datetime.now(timezone.utc)
        db.commit()

        logger.info("Scrape completed: %s", stats)
        return {
            "run_id": str(run.id),
            "products_found": len(total_products),
            **stats,
            "errors": len(total_errors),
        }

    except Exception as e:
        run.status = "failed"
        run.errors = total_errors[:99] + [str(e)]
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.exception("Scrape failed")
        raise
