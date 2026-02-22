import enum
from sqlalchemy import Column, Float, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class RefillStatus(str, enum.Enum):
    pending = "pending"
    on_time = "on_time"
    late = "late"
    missed = "missed"


class AdherenceRefill(TimestampMixin, Base):
    __tablename__ = "adherence_refills"
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("adherence_enrollments.id"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True, unique=True, index=True)
    due_date = Column(DateTime(timezone=True), nullable=False)
    actual_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(RefillStatus), nullable=False, default=RefillStatus.pending)
    discount_pct_applied = Column(Float, nullable=False, default=0)
    discount_amount = Column(Float, nullable=False, default=0)
    original_price = Column(Float, nullable=True)
    final_price = Column(Float, nullable=True)
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
