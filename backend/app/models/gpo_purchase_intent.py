import enum
from sqlalchemy import Column, String, Integer, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class IntentStatus(str, enum.Enum):
    submitted = "submitted"
    aggregated = "aggregated"
    cancelled = "cancelled"


class GpoPurchaseIntent(TimestampMixin, Base):
    __tablename__ = "gpo_purchase_intents"
    gpo_member_id = Column(UUID(as_uuid=True), ForeignKey("gpo_members.id"), nullable=False, index=True)
    cenabast_product_id = Column(UUID(as_uuid=True), ForeignKey("cenabast_products.id"), nullable=True, index=True)
    product_name = Column(String, nullable=True)
    quantity_units = Column(Integer, nullable=False)
    target_month = Column(String, nullable=False, index=True)
    status = Column(Enum(IntentStatus), nullable=False, default=IntentStatus.submitted)
    group_order_id = Column(UUID(as_uuid=True), ForeignKey("gpo_group_orders.id"), nullable=True, index=True)
