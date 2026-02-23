from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin


class ScrapeRun(TimestampMixin, Base):
    __tablename__ = "scrape_runs"

    chain = Column(String, nullable=False, index=True)
    status = Column(String, default="running")
    queries_total = Column(Integer, default=0)
    queries_completed = Column(Integer, default=0)
    products_found = Column(Integer, default=0)
    prices_upserted = Column(Integer, default=0)
    medications_created = Column(Integer, default=0)
    pharmacies_created = Column(Integer, default=0)
    errors = Column(JSON, default=list)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
