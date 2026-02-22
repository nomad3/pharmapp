import enum
from sqlalchemy import Column, String, Integer, Float, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class GroupOrderStatus(str, enum.Enum):
    intent_collection = "intent_collection"
    aggregated = "aggregated"
    submitted_to_cenabast = "submitted_to_cenabast"
    confirmed = "confirmed"
    fulfilled = "fulfilled"
    distributed = "distributed"


class GpoGroupOrder(TimestampMixin, Base):
    __tablename__ = "gpo_group_orders"
    gpo_group_id = Column(UUID(as_uuid=True), ForeignKey("gpo_groups.id"), nullable=False, index=True)
    cenabast_product_id = Column(UUID(as_uuid=True), ForeignKey("cenabast_products.id"), nullable=True, index=True)
    product_name = Column(String, nullable=True)
    target_month = Column(String, nullable=False, index=True)
    status = Column(Enum(GroupOrderStatus), nullable=False, default=GroupOrderStatus.intent_collection)
    total_quantity = Column(Integer, nullable=False, default=0)
    member_count = Column(Integer, nullable=False, default=0)
    unit_price_pmvp = Column(Float, nullable=True)
    unit_price_group = Column(Float, nullable=True)
    facilitation_fee = Column(Float, nullable=True)
