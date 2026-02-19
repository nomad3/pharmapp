from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geography
from app.models.base import Base, TimestampMixin

class SearchHistory(TimestampMixin, Base):
    __tablename__ = "search_history"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    query_text = Column(String, nullable=False)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    results_count = Column(Integer, default=0)
