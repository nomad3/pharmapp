import enum
from sqlalchemy import Column, String, Enum
from app.models.base import Base, TimestampMixin


class OrgType(str, enum.Enum):
    pharma = "pharma"
    pharmacy = "pharmacy"
    institution = "institution"
    api_consumer = "api_consumer"


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True, index=True)
    type = Column(Enum(OrgType), nullable=False, default=OrgType.api_consumer)
    stripe_customer_id = Column(String, nullable=True)
