import enum
from sqlalchemy import Column, String, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class SubscriptionTier(str, enum.Enum):
    free = "free"
    pro = "pro"
    enterprise = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    active = "active"
    canceled = "canceled"
    past_due = "past_due"


class Subscription(TimestampMixin, Base):
    __tablename__ = "subscriptions"

    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, unique=True, index=True)
    tier = Column(Enum(SubscriptionTier), nullable=False, default=SubscriptionTier.free)
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.active)
    stripe_subscription_id = Column(String, nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
