import uuid
from pydantic import BaseModel
from typing import Optional


class PriceAlertCreate(BaseModel):
    medication_id: uuid.UUID
    target_price: float


class PriceAlertOut(BaseModel):
    id: uuid.UUID
    medication_id: uuid.UUID
    target_price: float
    is_active: bool
    medication_name: Optional[str] = None
    last_notified_at: Optional[str] = None

    class Config:
        from_attributes = True


class PriceHistoryItem(BaseModel):
    date: str
    price: float
    pharmacy_chain: Optional[str] = None


class GenericAlternative(BaseModel):
    id: uuid.UUID
    name: str
    active_ingredient: Optional[str] = None
    lab: Optional[str] = None
    slug: Optional[str] = None
    min_price: Optional[float] = None


class UserSubscriptionOut(BaseModel):
    tier: str
    current_period_end: Optional[str] = None

    class Config:
        from_attributes = True


class PremiumCheckoutRequest(BaseModel):
    return_url: Optional[str] = None
