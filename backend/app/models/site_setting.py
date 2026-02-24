from sqlalchemy import Column, String, DateTime, func
from app.models.base import Base


class SiteSetting(Base):
    __tablename__ = "site_settings"
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False, default="")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
