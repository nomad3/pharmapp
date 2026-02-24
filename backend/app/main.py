import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import api_router
from app.models import Base
from app.core.database import engine
from app.middleware.rate_limit import RateLimitMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(title="PharmApp API")

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def on_startup():
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
