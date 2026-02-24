import hashlib

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.api_key import ApiKey
from app.models.organization import Organization
from app.models.org_member import OrgMember
from app.models.subscription import Subscription, SubscriptionTier
from app.models.user_subscription import UserSubscription, UserTier

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> Organization:
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    api_key = db.query(ApiKey).filter(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active == True,
    ).first()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    org = db.query(Organization).filter(Organization.id == api_key.org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Organization not found")

    sub = db.query(Subscription).filter(Subscription.org_id == org.id).first()
    tier = sub.tier.value if sub else "free"

    # Record usage (done after response in production, inline for simplicity)
    from app.models.api_usage import ApiUsage
    usage = ApiUsage(
        api_key_id=api_key.id,
        endpoint="",  # filled by middleware/route
        method="GET",
        status_code=200,
    )
    db.add(usage)
    db.commit()

    return org


def get_current_org_member(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    x_org_id: str = Header(None, alias="X-Org-Id"),
    db: Session = Depends(get_db),
):
    user = get_current_user(credentials, db)
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id header required")

    member = db.query(OrgMember).filter(
        OrgMember.org_id == x_org_id,
        OrgMember.user_id == user.id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    return {"user": user, "member": member, "org_id": x_org_id}


def require_premium_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    user = get_current_user(credentials, db)
    sub = db.query(UserSubscription).filter(UserSubscription.user_id == user.id).first()
    if not sub or sub.tier != UserTier.premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required",
        )
    return user


def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
