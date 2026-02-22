from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.models.org_member import OrgMember, OrgRole
from app.models.subscription import Subscription
from app.schemas.billing import CheckoutRequest, CheckoutResponse, PortalRequest, PortalResponse
from app.services import stripe_service

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(
    body: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.slug == body.org_slug).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    member = db.query(OrgMember).filter(
        OrgMember.org_id == org.id, OrgMember.user_id == user.id
    ).first()
    if not member or member.role not in (OrgRole.owner, OrgRole.admin):
        raise HTTPException(status_code=403, detail="Only owners/admins can manage billing")

    if not org.stripe_customer_id:
        org.stripe_customer_id = stripe_service.create_customer(org)
        db.commit()

    url = stripe_service.create_checkout_session(org, body.tier)
    return CheckoutResponse(checkout_url=url)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        result = stripe_service.handle_webhook(db, payload, sig)
    except Exception:
        raise HTTPException(status_code=400, detail="Webhook verification failed")
    return result


@router.post("/portal", response_model=PortalResponse)
def create_portal(
    body: PortalRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.slug == body.org_slug).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    member = db.query(OrgMember).filter(
        OrgMember.org_id == org.id, OrgMember.user_id == user.id
    ).first()
    if not member or member.role not in (OrgRole.owner, OrgRole.admin):
        raise HTTPException(status_code=403, detail="Only owners/admins can manage billing")

    if not org.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account set up")

    url = stripe_service.create_portal_session(org.stripe_customer_id)
    return PortalResponse(portal_url=url)
