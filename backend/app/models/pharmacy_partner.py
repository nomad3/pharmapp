from sqlalchemy import Column, String, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class PharmacyPartner(TimestampMixin, Base):
    __tablename__ = "pharmacy_partners"

    pharmacy_id = Column(UUID(as_uuid=True), ForeignKey("pharmacies.id"), nullable=False, unique=True, index=True)
    commission_rate = Column(Float, nullable=False, default=0.03)
    is_active = Column(Boolean, nullable=False, default=True)
    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
