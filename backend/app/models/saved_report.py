import enum
from sqlalchemy import Column, String, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class ReportSchedule(str, enum.Enum):
    none = "none"
    weekly = "weekly"
    monthly = "monthly"


class SavedReport(TimestampMixin, Base):
    __tablename__ = "saved_reports"
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    query_config = Column(JSON, nullable=False)
    schedule = Column(Enum(ReportSchedule), nullable=False, default=ReportSchedule.none)
    schedule_recipients = Column(String, nullable=True)
