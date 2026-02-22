from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_api_key
from app.schemas.report import ReportExecuteRequest, SavedReportCreate, SavedReportOut
from app.services.report_service import (
    execute_report,
    save_report,
    list_reports,
    delete_report,
    generate_csv,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/execute")
def execute(
    body: ReportExecuteRequest,
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    config = {
        "dataset": body.dataset,
        "filters": body.filters,
        "columns": body.columns,
        "sort_by": body.sort_by,
        "limit": body.limit,
    }
    return execute_report(db, config)


@router.post("/execute/csv")
def execute_csv(
    body: ReportExecuteRequest,
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    config = {
        "dataset": body.dataset,
        "filters": body.filters,
        "columns": body.columns,
        "sort_by": body.sort_by,
        "limit": body.limit,
    }
    data = execute_report(db, config)
    if isinstance(data, dict) and "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])

    csv_content = generate_csv(data)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={body.dataset}.csv"},
    )


@router.post("/save", response_model=SavedReportOut)
def save(
    body: SavedReportCreate,
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    return save_report(
        db,
        org_id=str(org.id),
        name=body.name,
        query_config=body.query_config,
        schedule=body.schedule,
        schedule_recipients=body.schedule_recipients,
    )


@router.get("/", response_model=list[SavedReportOut])
def list_all(
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    return list_reports(db, str(org.id))


@router.delete("/{report_id}")
def remove(
    report_id: str,
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    if not delete_report(db, report_id, str(org.id)):
        raise HTTPException(status_code=404, detail="Report not found")
    return {"status": "deleted"}
