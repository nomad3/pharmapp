import uuid
from datetime import datetime

from pydantic import BaseModel

class FavoriteCreate(BaseModel):
    medication_id: uuid.UUID

class FavoriteOut(BaseModel):
    id: uuid.UUID
    medication_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
