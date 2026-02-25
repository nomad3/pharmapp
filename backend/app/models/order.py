import enum
from sqlalchemy import Column, String, Float, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin

class OrderStatus(str, enum.Enum):
    pending = "pending"
    payment_sent = "payment_sent"
    pending_transfer = "pending_transfer"
    confirmed = "confirmed"
    delivering = "delivering"
    awaiting_delivery_payment = "awaiting_delivery_payment"
    completed = "completed"
    cancelled = "cancelled"

class PaymentProvider(str, enum.Enum):
    mercadopago = "mercadopago"
    transbank = "transbank"
    cash_on_delivery = "cash_on_delivery"
    bank_transfer = "bank_transfer"

class Order(TimestampMixin, Base):
    __tablename__ = "orders"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    pharmacy_id = Column(UUID(as_uuid=True), ForeignKey("pharmacies.id"), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending, nullable=False)
    payment_provider = Column(Enum(PaymentProvider), nullable=True)
    payment_url = Column(String, nullable=True)
    payment_status = Column(String, nullable=True)
    total = Column(Float, nullable=False, default=0)
