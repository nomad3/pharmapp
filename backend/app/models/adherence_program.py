import enum
from sqlalchemy import Column, String, Integer, Float, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class ProgramType(str, enum.Enum):
    platform = "platform"
    sponsored = "sponsored"


class AdherenceProgram(TimestampMixin, Base):
    __tablename__ = "adherence_programs"
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True, index=True)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"), nullable=False, index=True)
    program_type = Column(Enum(ProgramType), nullable=False, default=ProgramType.platform)
    refill_interval_days = Column(Integer, nullable=False, default=30)
    grace_period_days = Column(Integer, nullable=False, default=5)
    max_discount_pct = Column(Float, nullable=False, default=0.15)
