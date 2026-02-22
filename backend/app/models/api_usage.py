from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class ApiUsage(TimestampMixin, Base):
    __tablename__ = "api_usage"

    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False, index=True)
    endpoint = Column(String, nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
