import enum
from sqlalchemy import Column, String, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class ReferralEventType(str, enum.Enum):
    search = "search"
    view_prices = "view_prices"
    click_buy = "click_buy"
    order_created = "order_created"
    payment_completed = "payment_completed"


class ReferralEvent(TimestampMixin, Base):
    __tablename__ = "referral_events"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String, nullable=True, index=True)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"), nullable=True, index=True)
    pharmacy_id = Column(UUID(as_uuid=True), ForeignKey("pharmacies.id"), nullable=True, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True, index=True)
    event_type = Column(Enum(ReferralEventType), nullable=False, index=True)
