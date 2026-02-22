import enum
from sqlalchemy import Column, String, Float, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class CommissionStatus(str, enum.Enum):
    pending = "pending"
    invoiced = "invoiced"
    paid = "paid"


class Commission(TimestampMixin, Base):
    __tablename__ = "commissions"

    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, unique=True, index=True)
    pharmacy_partner_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_partners.id"), nullable=False, index=True)
    order_total = Column(Float, nullable=False)
    commission_rate = Column(Float, nullable=False)
    commission_amount = Column(Float, nullable=False)
    status = Column(Enum(CommissionStatus), nullable=False, default=CommissionStatus.pending)
