import asyncio

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.models.scrape_run import ScrapeRun

router = APIRouter(prefix="/scraping", tags=["scraping"])


@router.post("/run")
async def trigger_scrape(
    chains: list[str] | None = Query(None),
    query_limit: int = Query(200, ge=1, le=1000),
):
    """Trigger a scraping run in background via asyncio task."""
    from app.tasks.scraping import run_scrape_with_session
    asyncio.create_task(run_scrape_with_session(chains, query_limit))
    return {"status": "started", "chains": chains or ["all"], "query_limit": query_limit}


@router.get("/runs")
def list_scrape_runs(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    """List recent scrape runs."""
    runs = db.query(ScrapeRun).order_by(ScrapeRun.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "chain": r.chain,
            "status": r.status,
            "queries_total": r.queries_total,
            "queries_completed": r.queries_completed,
            "products_found": r.products_found,
            "prices_upserted": r.prices_upserted,
            "medications_created": r.medications_created,
            "errors_count": len(r.errors or []),
            "started_at": str(r.started_at),
            "finished_at": str(r.finished_at) if r.finished_at else None,
        }
        for r in runs
    ]


@router.get("/runs/{run_id}")
def get_scrape_run(run_id: str, db: Session = Depends(get_db)):
    """Get details of a specific scrape run, including errors."""
    run = db.query(ScrapeRun).filter(ScrapeRun.id == run_id).first()
    if not run:
        return {"error": "Not found"}
    return {
        "id": str(run.id),
        "chain": run.chain,
        "status": run.status,
        "queries_total": run.queries_total,
        "queries_completed": run.queries_completed,
        "products_found": run.products_found,
        "prices_upserted": run.prices_upserted,
        "medications_created": run.medications_created,
        "pharmacies_created": run.pharmacies_created,
        "errors": run.errors,
        "started_at": str(run.started_at),
        "finished_at": str(run.finished_at) if run.finished_at else None,
    }


@router.post("/locations")
async def trigger_location_scrape(
    chains: list[str] | None = Query(None),
):
    """Trigger a location scraping run in background."""
    from app.tasks.scraping import run_location_scrape_with_session
    asyncio.create_task(run_location_scrape_with_session(chains))
    return {"status": "started", "type": "locations", "chains": chains or ["all"]}


@router.post("/catalog")
async def trigger_catalog_scrape(
    chains: list[str] | None = Query(None),
):
    """Trigger a full catalog scraping run in background.

    Browses the entire Medicamentos category for each chain.
    """
    from app.tasks.scraping import run_catalog_scrape_with_session
    asyncio.create_task(run_catalog_scrape_with_session(chains))
    return {"status": "started", "type": "catalog", "chains": chains or ["all"]}


@router.get("/schedule")
def get_schedule(db: Session = Depends(get_db)):
    """Get scheduled scraping info and last run details."""
    last_run = (
        db.query(ScrapeRun)
        .filter(ScrapeRun.status.in_(["completed", "failed"]))
        .order_by(ScrapeRun.finished_at.desc())
        .first()
    )
    return {
        "schedule": {
            "catalog_scrape": "Daily at 3:00 AM UTC",
            "price_alerts": "Every 6 hours",
        },
        "last_run": {
            "id": str(last_run.id),
            "chain": last_run.chain,
            "status": last_run.status,
            "products_found": last_run.products_found,
            "finished_at": str(last_run.finished_at) if last_run.finished_at else None,
        } if last_run else None,
    }
