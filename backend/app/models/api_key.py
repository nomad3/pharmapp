from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class ApiKey(TimestampMixin, Base):
    __tablename__ = "api_keys"

    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    key_prefix = Column(String(8), nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
