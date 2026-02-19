import enum
from sqlalchemy import Column, String, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin

class DeliveryStatus(str, enum.Enum):
    assigned = "assigned"
    picked_up = "picked_up"
    in_transit = "in_transit"
    delivered = "delivered"

class OrderDelivery(TimestampMixin, Base):
    __tablename__ = "order_deliveries"
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, unique=True)
    delivery_address_id = Column(UUID(as_uuid=True), ForeignKey("delivery_addresses.id"), nullable=False)
    rider_name = Column(String, nullable=True)
    rider_phone = Column(String, nullable=True)
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.assigned)
    eta = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
