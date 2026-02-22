import uuid
from pydantic import BaseModel
from typing import Optional


class ApiKeyCreate(BaseModel):
    name: str
    org_slug: str


class ApiKeyCreated(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    key: str  # plaintext, shown only once

    class Config:
        from_attributes = True


class ApiKeyOut(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    is_active: bool
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class UsageStats(BaseModel):
    total_requests: int = 0
    requests_today: int = 0
    avg_response_time_ms: float = 0
    top_endpoints: list = []
