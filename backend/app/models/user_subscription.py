import enum
from sqlalchemy import Column, String, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class UserTier(str, enum.Enum):
    free = "free"
    premium = "premium"


class UserSubscription(TimestampMixin, Base):
    __tablename__ = "user_subscriptions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    tier = Column(Enum(UserTier), nullable=False, default=UserTier.free)
    stripe_subscription_id = Column(String, nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
