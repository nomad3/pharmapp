from pydantic import BaseModel
from app.schemas.pharmacy import PharmacyOut

class PriceOut(BaseModel):
    id: str
    medication_id: str
    pharmacy_id: str
    price: float
    in_stock: bool
    scraped_at: str | None

    class Config:
        from_attributes = True

class PriceCompareItem(BaseModel):
    price: float
    in_stock: bool
    pharmacy: PharmacyOut
    distance_km: float | None = None
