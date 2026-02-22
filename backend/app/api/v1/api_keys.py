import hashlib
import secrets
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.models.org_member import OrgMember, OrgRole
from app.models.api_key import ApiKey
from app.models.api_usage import ApiUsage
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreated, ApiKeyOut, UsageStats

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("/", response_model=ApiKeyCreated)
def create_api_key(
    body: ApiKeyCreate,
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
        raise HTTPException(status_code=403, detail="Only owners/admins can create API keys")

    raw_key = "pa_live_" + secrets.token_hex(16)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[8:16]  # first 8 chars after prefix

    api_key = ApiKey(
        org_id=org.id,
        name=body.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return ApiKeyCreated(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        key=raw_key,
    )


@router.get("/", response_model=list[ApiKeyOut])
def list_api_keys(
    org_slug: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.slug == org_slug).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    member = db.query(OrgMember).filter(
        OrgMember.org_id == org.id, OrgMember.user_id == user.id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")

    keys = db.query(ApiKey).filter(ApiKey.org_id == org.id).order_by(ApiKey.created_at.desc()).all()
    return [
        ApiKeyOut(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            is_active=k.is_active,
            created_at=str(k.created_at) if k.created_at else None,
        )
        for k in keys
    ]


@router.delete("/{key_id}")
def revoke_api_key(
    key_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    member = db.query(OrgMember).filter(
        OrgMember.org_id == api_key.org_id, OrgMember.user_id == user.id
    ).first()
    if not member or member.role not in (OrgRole.owner, OrgRole.admin):
        raise HTTPException(status_code=403, detail="Only owners/admins can revoke keys")

    api_key.is_active = False
    db.commit()
    return {"status": "revoked"}


@router.get("/{key_id}/usage", response_model=UsageStats)
def get_usage(
    key_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    member = db.query(OrgMember).filter(
        OrgMember.org_id == api_key.org_id, OrgMember.user_id == user.id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")

    total = db.query(func.count(ApiUsage.id)).filter(ApiUsage.api_key_id == api_key.id).scalar() or 0
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today = db.query(func.count(ApiUsage.id)).filter(
        ApiUsage.api_key_id == api_key.id,
        ApiUsage.timestamp >= today_start,
    ).scalar() or 0

    avg_rt = db.query(func.avg(ApiUsage.response_time_ms)).filter(
        ApiUsage.api_key_id == api_key.id
    ).scalar() or 0

    top = db.query(
        ApiUsage.endpoint,
        func.count(ApiUsage.id).label("count"),
    ).filter(ApiUsage.api_key_id == api_key.id).group_by(
        ApiUsage.endpoint
    ).order_by(func.count(ApiUsage.id).desc()).limit(5).all()

    return UsageStats(
        total_requests=total,
        requests_today=today,
        avg_response_time_ms=round(float(avg_rt), 1),
        top_endpoints=[{"endpoint": r.endpoint, "count": r.count} for r in top],
    )
