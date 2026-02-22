import enum
from sqlalchemy import Column, Float, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class FeeStatus(str, enum.Enum):
    pending = "pending"
    invoiced = "invoiced"
    paid = "paid"


class GpoFacilitationFee(TimestampMixin, Base):
    __tablename__ = "gpo_facilitation_fees"
    group_order_id = Column(UUID(as_uuid=True), ForeignKey("gpo_group_orders.id"), nullable=False, unique=True, index=True)
    order_total = Column(Float, nullable=False)
    fee_rate = Column(Float, nullable=False)
    fee_amount = Column(Float, nullable=False)
    status = Column(Enum(FeeStatus), nullable=False, default=FeeStatus.pending)
