from sqlalchemy import Column, String
from geoalchemy2 import Geography
from app.models.base import Base, TimestampMixin

class User(TimestampMixin, Base):
    __tablename__ = "users"
    phone_number = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    comuna = Column(String, nullable=True)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
