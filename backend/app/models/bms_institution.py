from sqlalchemy import Column, String, Integer

from app.models.base import Base, TimestampMixin


class BmsInstitution(TimestampMixin, Base):
    __tablename__ = "bms_institutions"

    rut = Column(String, unique=True, index=True, nullable=False)
    client_code = Column(Integer, nullable=True)
    razon_social = Column(String, nullable=True)
    region = Column(String, nullable=True)
    comuna = Column(String, nullable=True)
