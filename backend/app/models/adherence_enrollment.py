import enum
from sqlalchemy import Column, String, Integer, Float, Boolean, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class EnrollmentStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    completed = "completed"
    dropped = "dropped"


class AdherenceEnrollment(TimestampMixin, Base):
    __tablename__ = "adherence_enrollments"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    program_id = Column(UUID(as_uuid=True), ForeignKey("adherence_programs.id"), nullable=False, index=True)
    pharmacy_partner_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_partners.id"), nullable=True, index=True)
    status = Column(Enum(EnrollmentStatus), nullable=False, default=EnrollmentStatus.active)
    consecutive_on_time = Column(Integer, nullable=False, default=0)
    total_refills = Column(Integer, nullable=False, default=0)
    total_on_time = Column(Integer, nullable=False, default=0)
    total_late = Column(Integer, nullable=False, default=0)
    total_missed = Column(Integer, nullable=False, default=0)
    adherence_score = Column(Float, nullable=False, default=0)
    current_discount_pct = Column(Float, nullable=False, default=0)
    next_refill_due = Column(DateTime(timezone=True), nullable=True)
    whatsapp_consent = Column(Boolean, nullable=False, default=True)
