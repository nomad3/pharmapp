import uuid
from pydantic import BaseModel
from typing import Optional


class OrgCreate(BaseModel):
    name: str
    type: str = "api_consumer"


class OrgUpdate(BaseModel):
    name: Optional[str] = None


class OrgOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    type: str
    stripe_customer_id: Optional[str] = None

    class Config:
        from_attributes = True


class MemberInvite(BaseModel):
    phone_number: str
    role: str = "viewer"


class MemberOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    role: str
    user_phone: Optional[str] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True
