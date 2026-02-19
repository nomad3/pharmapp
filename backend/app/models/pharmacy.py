from sqlalchemy import Column, String
from geoalchemy2 import Geography
from app.models.base import Base, TimestampMixin

class Pharmacy(TimestampMixin, Base):
    __tablename__ = "pharmacies"
    chain = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    comuna = Column(String, nullable=False, index=True)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    phone = Column(String, nullable=True)
    hours = Column(String, nullable=True)
