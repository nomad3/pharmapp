import uuid
from datetime import datetime
from pydantic import BaseModel


class GpoGroupCreate(BaseModel):
    name: str
    slug: str
    tier: str = "basic"
    facilitation_fee_rate: float = 0.02
    min_aggregation_threshold: int = 100


class GpoGroupOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    tier: str
    facilitation_fee_rate: float
    min_aggregation_threshold: int
    created_at: datetime

    class Config:
        from_attributes = True


class GpoMemberCreate(BaseModel):
    rut: str | None = None
    institution_name: str | None = None
    institution_type: str = "pharmacy"
    role: str = "member"
    monthly_volume_estimate: float | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    org_id: str | None = None


class GpoMemberOut(BaseModel):
    id: uuid.UUID
    gpo_group_id: uuid.UUID
    org_id: uuid.UUID | None = None
    rut: str | None = None
    institution_name: str | None = None
    institution_type: str
    role: str
    monthly_volume_estimate: float | None = None
    contact_phone: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class PurchaseIntentCreate(BaseModel):
    cenabast_product_id: str | None = None
    product_name: str | None = None
    quantity_units: int
    target_month: str


class PurchaseIntentOut(BaseModel):
    id: uuid.UUID
    gpo_member_id: uuid.UUID
    cenabast_product_id: uuid.UUID | None = None
    product_name: str | None = None
    quantity_units: int
    target_month: str
    status: str
    group_order_id: uuid.UUID | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class GroupOrderOut(BaseModel):
    id: uuid.UUID
    gpo_group_id: uuid.UUID
    product_name: str | None = None
    target_month: str
    status: str
    total_quantity: int
    member_count: int
    unit_price_pmvp: float | None = None
    unit_price_group: float | None = None
    facilitation_fee: float | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class GroupOrderStatusUpdate(BaseModel):
    status: str


class AllocationOut(BaseModel):
    id: uuid.UUID
    group_order_id: uuid.UUID
    gpo_member_id: uuid.UUID
    quantity_allocated: int
    unit_price: float
    subtotal: float
    facilitation_fee: float
    status: str

    class Config:
        from_attributes = True


class AggregatedDemandOut(BaseModel):
    product_name: str
    cenabast_product_id: str | None = None
    total_quantity: int
    member_count: int
    threshold: int
    threshold_met: bool


class SavingsOut(BaseModel):
    total_orders: int
    total_pmvp_cost: float
    total_group_cost: float
    total_savings: float
    savings_pct: float


class MemberSavingsSummary(BaseModel):
    member_id: str
    institution_name: str | None = None
    total_savings: float
    order_count: int
