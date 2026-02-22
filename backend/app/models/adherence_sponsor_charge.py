import enum
from sqlalchemy import Column, String, Float, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class ChargeType(str, enum.Enum):
    enrollment = "enrollment"
    refill = "refill"
    discount_coverage = "discount_coverage"


class ChargeStatus(str, enum.Enum):
    pending = "pending"
    invoiced = "invoiced"
    paid = "paid"


class AdherenceSponsorCharge(TimestampMixin, Base):
    __tablename__ = "adherence_sponsor_charges"
    sponsor_id = Column(UUID(as_uuid=True), ForeignKey("adherence_sponsors.id"), nullable=False, index=True)
    refill_id = Column(UUID(as_uuid=True), ForeignKey("adherence_refills.id"), nullable=True, index=True)
    charge_type = Column(Enum(ChargeType), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(ChargeStatus), nullable=False, default=ChargeStatus.pending)
