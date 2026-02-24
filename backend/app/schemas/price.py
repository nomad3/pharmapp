import uuid

from pydantic import BaseModel
from app.schemas.pharmacy import PharmacyOut

class PriceOut(BaseModel):
    id: uuid.UUID
    medication_id: uuid.UUID
    pharmacy_id: uuid.UUID
    price: float
    in_stock: bool
    scraped_at: str | None

    class Config:
        from_attributes = True

class PriceCompareItem(BaseModel):
    price_id: uuid.UUID
    price: float
    in_stock: bool
    pharmacy: PharmacyOut
    distance_km: float | None = None
