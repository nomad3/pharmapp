import uuid
from datetime import datetime
from pydantic import BaseModel


class ReportExecuteRequest(BaseModel):
    dataset: str
    filters: dict = {}
    columns: list[str] = []
    sort_by: str | None = None
    limit: int = 100


class SavedReportCreate(BaseModel):
    name: str
    query_config: dict
    schedule: str = "none"
    schedule_recipients: str | None = None


class SavedReportOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    query_config: dict
    schedule: str
    schedule_recipients: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
