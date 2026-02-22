import uuid
from pydantic import BaseModel
from typing import Optional


class CommissionOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    pharmacy_partner_id: uuid.UUID
    order_total: float
    commission_rate: float
    commission_amount: float
    status: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class CommissionSummary(BaseModel):
    pharmacy_name: Optional[str] = None
    month: str
    total_orders: int = 0
    total_order_amount: float = 0
    total_commission: float = 0


class PharmacyPartnerOut(BaseModel):
    id: uuid.UUID
    pharmacy_id: uuid.UUID
    commission_rate: float
    is_active: bool
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None

    class Config:
        from_attributes = True
