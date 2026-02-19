from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin

class UserFavorite(TimestampMixin, Base):
    __tablename__ = "user_favorites"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"), nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "medication_id"),)
