from sqlalchemy import Column, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class PriceAlert(TimestampMixin, Base):
    __tablename__ = "price_alerts"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"), nullable=False, index=True)
    target_price = Column(Float, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_notified_at = Column(DateTime(timezone=True), nullable=True)
