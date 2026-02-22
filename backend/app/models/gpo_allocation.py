import enum
from sqlalchemy import Column, Integer, Float, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class AllocationStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"


class GpoAllocation(TimestampMixin, Base):
    __tablename__ = "gpo_allocations"
    group_order_id = Column(UUID(as_uuid=True), ForeignKey("gpo_group_orders.id"), nullable=False, index=True)
    gpo_member_id = Column(UUID(as_uuid=True), ForeignKey("gpo_members.id"), nullable=False, index=True)
    quantity_allocated = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    facilitation_fee = Column(Float, nullable=False, default=0)
    status = Column(Enum(AllocationStatus), nullable=False, default=AllocationStatus.pending)
