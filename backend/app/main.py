import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.v1.routes import api_router
from app.models import Base
from app.core.database import engine
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIdMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(title="Remedia API")

app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health_check():
    """Health check for monitoring and Docker."""
    from app.core.database import SessionLocal
    from app.models.scrape_run import ScrapeRun

    db_ok = False
    scrape_age_hours = None

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db_ok = True

        last_scrape = db.query(ScrapeRun).order_by(ScrapeRun.finished_at.desc()).first()
        if last_scrape and last_scrape.finished_at:
            age = (datetime.now(timezone.utc) - last_scrape.finished_at).total_seconds()
            scrape_age_hours = round(age / 3600, 1)
        db.close()
    except Exception:
        pass

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "ok" if db_ok else "error",
        "last_scrape_hours_ago": scrape_age_hours,
    }


@app.on_event("startup")
def on_startup():
    # Add new enum values to PostgreSQL (idempotent)
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        db.execute(text("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'pending_transfer'"))
        db.execute(text("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'awaiting_delivery_payment'"))
        db.execute(text("ALTER TYPE paymentprovider ADD VALUE IF NOT EXISTS 'cash_on_delivery'"))
        db.execute(text("ALTER TYPE paymentprovider ADD VALUE IF NOT EXISTS 'bank_transfer'"))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    Base.metadata.create_all(bind=engine)

    # Start background scheduler for price alerts and auto-scraping
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from app.tasks.price_alerts import check_price_alerts
        from app.tasks.scheduled import run_scheduled_scrape

        scheduler = AsyncIOScheduler()
        scheduler.add_job(check_price_alerts, "interval", hours=6, id="price_alerts")
        scheduler.add_job(run_scheduled_scrape, "cron", hour=3, id="daily_scrape")
        scheduler.start()
        logger.info("Scheduler started: price alerts every 6h, catalog scrape daily at 3AM")
    except Exception:
        logger.warning("Scheduler failed to start (non-fatal)", exc_info=True)
