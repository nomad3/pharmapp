import enum
from sqlalchemy import Column, String, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class OrgRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class OrgMember(TimestampMixin, Base):
    __tablename__ = "org_members"
    __table_args__ = (UniqueConstraint("org_id", "user_id", name="uq_org_member"),)

    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(Enum(OrgRole), nullable=False, default=OrgRole.viewer)
