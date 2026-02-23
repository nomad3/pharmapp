from sqlalchemy import Column, String, Boolean, event
from app.models.base import Base, TimestampMixin
from app.utils.slugify import medication_slug


class Medication(TimestampMixin, Base):
    __tablename__ = "medications"
    name = Column(String, nullable=False, index=True)
    active_ingredient = Column(String, nullable=True, index=True)
    dosage = Column(String, nullable=True)
    form = Column(String, nullable=True)
    lab = Column(String, nullable=True)
    slug = Column(String, nullable=True, unique=True, index=True)
    isp_registry_number = Column(String, nullable=True, unique=True)
    requires_prescription = Column(Boolean, default=False)


@event.listens_for(Medication, "before_insert")
def generate_slug_before_insert(mapper, connection, target):
    """Auto-generate slug if not already set."""
    if not target.slug and target.name:
        target.slug = medication_slug(target.name, target.dosage, target.lab)
