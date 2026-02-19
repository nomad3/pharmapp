from sqlalchemy import Column, Float, Boolean, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin

class Price(TimestampMixin, Base):
    __tablename__ = "prices"
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"), nullable=False, index=True)
    pharmacy_id = Column(UUID(as_uuid=True), ForeignKey("pharmacies.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    in_stock = Column(Boolean, default=True)
    source_url = Column(String, nullable=True)
    scraped_at = Column(DateTime(timezone=True), nullable=True)
