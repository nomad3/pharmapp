from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class AdherenceDiscountTier(TimestampMixin, Base):
    __tablename__ = "adherence_discount_tiers"
    program_id = Column(UUID(as_uuid=True), ForeignKey("adherence_programs.id"), nullable=False, index=True)
    min_consecutive_refills = Column(Integer, nullable=False)
    max_consecutive_refills = Column(Integer, nullable=True)
    discount_pct = Column(Float, nullable=False)
