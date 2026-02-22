from sqlalchemy import Column, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class PharmacyDiscountCap(TimestampMixin, Base):
    __tablename__ = "pharmacy_discount_caps"
    pharmacy_partner_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_partners.id"), nullable=False, index=True)
    program_id = Column(UUID(as_uuid=True), ForeignKey("adherence_programs.id"), nullable=False, index=True)
    max_discount_pct = Column(Float, nullable=False, default=0.15)
