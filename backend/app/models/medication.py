from sqlalchemy import Column, String, Boolean
from app.models.base import Base, TimestampMixin

class Medication(TimestampMixin, Base):
    __tablename__ = "medications"
    name = Column(String, nullable=False, index=True)
    active_ingredient = Column(String, nullable=True, index=True)
    dosage = Column(String, nullable=True)
    form = Column(String, nullable=True)
    lab = Column(String, nullable=True)
    isp_registry_number = Column(String, nullable=True, unique=True)
    requires_prescription = Column(Boolean, default=False)
