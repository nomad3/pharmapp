from pydantic import BaseModel
from typing import Optional


class CheckoutRequest(BaseModel):
    tier: str  # "pro" or "enterprise"
    org_slug: str


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalRequest(BaseModel):
    org_slug: str


class PortalResponse(BaseModel):
    portal_url: str


class SubscriptionOut(BaseModel):
    tier: str
    status: str
    current_period_end: Optional[str] = None

    class Config:
        from_attributes = True
