from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geography
from app.models.base import Base, TimestampMixin

class DeliveryAddress(TimestampMixin, Base):
    __tablename__ = "delivery_addresses"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    label = Column(String, default="home")
    address = Column(String, nullable=False)
    comuna = Column(String, nullable=False)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    instructions = Column(Text, nullable=True)
