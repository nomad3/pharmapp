import uuid
from datetime import datetime

from pydantic import BaseModel

class OrderItemCreate(BaseModel):
    medication_id: uuid.UUID
    price_id: uuid.UUID
    quantity: int = 1

class OrderCreate(BaseModel):
    pharmacy_id: uuid.UUID
    items: list[OrderItemCreate]
    payment_provider: str
    delivery_address_id: uuid.UUID | None = None

class OrderOut(BaseModel):
    id: uuid.UUID
    status: str
    payment_provider: str | None
    payment_url: str | None
    total: float
    created_at: datetime

    class Config:
        from_attributes = True
