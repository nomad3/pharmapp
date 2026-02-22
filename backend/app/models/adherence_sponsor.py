from sqlalchemy import Column, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class AdherenceSponsor(TimestampMixin, Base):
    __tablename__ = "adherence_sponsors"
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    program_id = Column(UUID(as_uuid=True), ForeignKey("adherence_programs.id"), nullable=False, index=True)
    budget_total = Column(Float, nullable=False, default=0)
    budget_remaining = Column(Float, nullable=False, default=0)
    cost_per_enrollment = Column(Float, nullable=False, default=0)
    cost_per_refill = Column(Float, nullable=False, default=0)
    discount_coverage_pct = Column(Float, nullable=False, default=1.0)
