import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.organization import Organization, OrgType
from app.models.org_member import OrgMember, OrgRole
from app.models.subscription import Subscription, SubscriptionTier, SubscriptionStatus
from app.schemas.organization import OrgCreate, OrgUpdate, OrgOut, MemberInvite, MemberOut

router = APIRouter(prefix="/organizations", tags=["organizations"])


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug


@router.post("/", response_model=OrgOut)
def create_org(
    body: OrgCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    slug = _slugify(body.name)
    existing = db.query(Organization).filter(Organization.slug == slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Organization slug already exists")

    org = Organization(
        name=body.name,
        slug=slug,
        type=OrgType(body.type) if body.type in [t.value for t in OrgType] else OrgType.api_consumer,
    )
    db.add(org)
    db.flush()

    member = OrgMember(org_id=org.id, user_id=user.id, role=OrgRole.owner)
    db.add(member)

    sub = Subscription(
        org_id=org.id,
        tier=SubscriptionTier.free,
        status=SubscriptionStatus.active,
    )
    db.add(sub)

    db.commit()
    db.refresh(org)
    return org


@router.get("/{slug}", response_model=OrgOut)
def get_org(
    slug: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.slug == slug).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    member = db.query(OrgMember).filter(
        OrgMember.org_id == org.id, OrgMember.user_id == user.id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    return org


@router.put("/{slug}", response_model=OrgOut)
def update_org(
    slug: str,
    body: OrgUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.slug == slug).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    member = db.query(OrgMember).filter(
        OrgMember.org_id == org.id, OrgMember.user_id == user.id
    ).first()
    if not member or member.role not in (OrgRole.owner, OrgRole.admin):
        raise HTTPException(status_code=403, detail="Only owners/admins can update")

    if body.name:
        org.name = body.name
    db.commit()
    db.refresh(org)
    return org


@router.get("/{slug}/members", response_model=list[MemberOut])
def list_members(
    slug: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.slug == slug).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    member = db.query(OrgMember).filter(
        OrgMember.org_id == org.id, OrgMember.user_id == user.id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")

    members = db.query(OrgMember).filter(OrgMember.org_id == org.id).all()
    result = []
    for m in members:
        u = db.query(User).filter(User.id == m.user_id).first()
        result.append(MemberOut(
            id=m.id,
            user_id=m.user_id,
            role=m.role.value,
            user_phone=u.phone_number if u else None,
            user_name=u.name if u else None,
        ))
    return result


@router.post("/{slug}/members", response_model=MemberOut)
def invite_member(
    slug: str,
    body: MemberInvite,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.slug == slug).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    member = db.query(OrgMember).filter(
        OrgMember.org_id == org.id, OrgMember.user_id == user.id
    ).first()
    if not member or member.role not in (OrgRole.owner, OrgRole.admin):
        raise HTTPException(status_code=403, detail="Only owners/admins can invite")

    target = db.query(User).filter(User.phone_number == body.phone_number).first()
    if not target:
        target = User(phone_number=body.phone_number)
        db.add(target)
        db.flush()

    existing = db.query(OrgMember).filter(
        OrgMember.org_id == org.id, OrgMember.user_id == target.id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already a member")

    new_member = OrgMember(
        org_id=org.id,
        user_id=target.id,
        role=OrgRole(body.role) if body.role in [r.value for r in OrgRole] else OrgRole.viewer,
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    return MemberOut(
        id=new_member.id,
        user_id=new_member.user_id,
        role=new_member.role.value,
        user_phone=target.phone_number,
        user_name=target.name,
    )


@router.delete("/{slug}/members/{user_id}")
def remove_member(
    slug: str,
    user_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.slug == slug).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    member = db.query(OrgMember).filter(
        OrgMember.org_id == org.id, OrgMember.user_id == user.id
    ).first()
    if not member or member.role not in (OrgRole.owner, OrgRole.admin):
        raise HTTPException(status_code=403, detail="Only owners/admins can remove members")

    target = db.query(OrgMember).filter(
        OrgMember.org_id == org.id, OrgMember.user_id == user_id
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    db.delete(target)
    db.commit()
    return {"status": "removed"}
