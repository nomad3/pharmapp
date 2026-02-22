import enum
from sqlalchemy import Column, String, Float, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin


class GpoInstitutionType(str, enum.Enum):
    pharmacy = "pharmacy"
    clinic = "clinic"
    hospital = "hospital"
    ngo = "ngo"


class GpoMemberRole(str, enum.Enum):
    admin = "admin"
    member = "member"


class GpoMember(TimestampMixin, Base):
    __tablename__ = "gpo_members"
    gpo_group_id = Column(UUID(as_uuid=True), ForeignKey("gpo_groups.id"), nullable=False, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    rut = Column(String, nullable=True, index=True)
    institution_name = Column(String, nullable=True)
    institution_type = Column(Enum(GpoInstitutionType), nullable=False, default=GpoInstitutionType.pharmacy)
    role = Column(Enum(GpoMemberRole), nullable=False, default=GpoMemberRole.member)
    monthly_volume_estimate = Column(Float, nullable=True)
    contact_phone = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
