from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.models.scrape_run import ScrapeRun

router = APIRouter(prefix="/scraping", tags=["scraping"])


@router.post("/run")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    chains: list[str] | None = Query(None),
    query_limit: int = Query(200, ge=1, le=1000),
):
    """Trigger a scraping run. Runs in background with its own DB session."""
    from app.tasks.scraping import run_scrape_with_session
    background_tasks.add_task(run_scrape_with_session, chains, query_limit)
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
