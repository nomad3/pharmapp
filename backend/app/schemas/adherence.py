import uuid
from datetime import datetime
from pydantic import BaseModel


class AdherenceProgramOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    medication_id: uuid.UUID
    program_type: str
    refill_interval_days: int
    grace_period_days: int
    max_discount_pct: float
    created_at: datetime

    class Config:
        from_attributes = True


class DiscountTierOut(BaseModel):
    id: uuid.UUID
    program_id: uuid.UUID
    min_consecutive_refills: int
    max_consecutive_refills: int | None = None
    discount_pct: float

    class Config:
        from_attributes = True


class EnrollmentCreate(BaseModel):
    program_id: str
    pharmacy_partner_id: str | None = None
    whatsapp_consent: bool = True


class EnrollmentOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    program_id: uuid.UUID
    pharmacy_partner_id: uuid.UUID | None = None
    status: str
    consecutive_on_time: int
    total_refills: int
    adherence_score: float
    current_discount_pct: float
    next_refill_due: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class RefillOut(BaseModel):
    id: uuid.UUID
    enrollment_id: uuid.UUID
    order_id: uuid.UUID | None = None
    due_date: datetime
    actual_date: datetime | None = None
    status: str
    discount_pct_applied: float
    discount_amount: float
    original_price: float | None = None
    final_price: float | None = None

    class Config:
        from_attributes = True


class AdherenceDashboardOut(BaseModel):
    enrollments: list[dict]
    total_savings: float
    avg_adherence_score: float


class AdherenceSavingsHistory(BaseModel):
    total_discount_amount: float
    refill_count: int
    avg_discount_pct: float


class SponsorProgramOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    program_id: uuid.UUID
    budget_total: float
    budget_remaining: float
    cost_per_enrollment: float
    cost_per_refill: float
    discount_coverage_pct: float

    class Config:
        from_attributes = True


class SponsorChargeOut(BaseModel):
    id: uuid.UUID
    sponsor_id: uuid.UUID
    refill_id: uuid.UUID | None = None
    charge_type: str
    amount: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PharmacyAdherenceOut(BaseModel):
    program_count: int
    total_enrollments: int
    avg_adherence_score: float


class ProgramCreateRequest(BaseModel):
    name: str
    slug: str
    medication_id: str
    program_type: str = "platform"
    refill_interval_days: int = 30
    grace_period_days: int = 5
    max_discount_pct: float = 0.15


class TierCreateRequest(BaseModel):
    min_consecutive_refills: int
    max_consecutive_refills: int | None = None
    discount_pct: float


class SponsorAttachRequest(BaseModel):
    org_id: str
    budget_total: float
    cost_per_enrollment: float = 0
    cost_per_refill: float = 0
    discount_coverage_pct: float = 1.0


class DiscountCapUpdate(BaseModel):
    program_id: str
    max_discount_pct: float
