import enum
from sqlalchemy import Column, String, Float, Enum, Integer
from app.models.base import Base, TimestampMixin


class GpoTier(str, enum.Enum):
    basic = "basic"
    premium = "premium"


class GpoGroup(TimestampMixin, Base):
    __tablename__ = "gpo_groups"
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True, index=True)
    tier = Column(Enum(GpoTier), nullable=False, default=GpoTier.basic)
    facilitation_fee_rate = Column(Float, nullable=False, default=0.02)
    min_aggregation_threshold = Column(Integer, nullable=False, default=100)
