from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin

class OrderItem(TimestampMixin, Base):
    __tablename__ = "order_items"
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"), nullable=False)
    price_id = Column(UUID(as_uuid=True), ForeignKey("prices.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    subtotal = Column(Float, nullable=False)
