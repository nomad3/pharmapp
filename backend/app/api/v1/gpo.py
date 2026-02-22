from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.gpo_group import GpoGroup
from app.models.gpo_member import GpoMember, GpoMemberRole
from app.models.gpo_purchase_intent import GpoPurchaseIntent, IntentStatus
from app.models.gpo_group_order import GpoGroupOrder
from app.models.gpo_allocation import GpoAllocation
from app.models.gpo_facilitation_fee import GpoFacilitationFee
from app.schemas.gpo import (
    GpoGroupCreate, GpoGroupOut,
    GpoMemberCreate, GpoMemberOut,
    PurchaseIntentCreate, PurchaseIntentOut,
    GroupOrderOut, GroupOrderStatusUpdate,
    AllocationOut,
)
from app.services.gpo_service import (
    get_aggregated_demand,
    create_group_order_from_demand,
    update_group_order_status,
    get_group_savings,
    get_member_savings,
)

router = APIRouter(prefix="/gpo", tags=["gpo"])


def _get_group(db: Session, slug: str) -> GpoGroup:
    group = db.query(GpoGroup).filter(GpoGroup.slug == slug).first()
    if not group:
        raise HTTPException(status_code=404, detail="GPO group not found")
    return group


def _get_member(db: Session, group_id, user: User) -> GpoMember:
    member = db.query(GpoMember).filter(
        GpoMember.gpo_group_id == group_id,
        GpoMember.org_id.isnot(None),
    ).first()
    return member


def _require_admin(db: Session, group_id, user: User) -> GpoMember:
    member = db.query(GpoMember).filter(
        GpoMember.gpo_group_id == group_id,
        GpoMember.role == GpoMemberRole.admin,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="GPO admin role required")
    return member


# ── Group CRUD ──

@router.post("/groups", response_model=GpoGroupOut)
def create_group(
    body: GpoGroupCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing = db.query(GpoGroup).filter(GpoGroup.slug == body.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Group slug already exists")

    group = GpoGroup(**body.model_dump())
    db.add(group)
    db.flush()

    # Creator becomes admin
    admin = GpoMember(
        gpo_group_id=group.id,
        role=GpoMemberRole.admin,
        institution_type="pharmacy",
    )
    db.add(admin)
    db.commit()
    db.refresh(group)
    return group


@router.get("/groups", response_model=list[GpoGroupOut])
def list_groups(db: Session = Depends(get_db)):
    return db.query(GpoGroup).order_by(GpoGroup.created_at.desc()).all()


@router.get("/groups/{slug}", response_model=GpoGroupOut)
def get_group(slug: str, db: Session = Depends(get_db)):
    return _get_group(db, slug)


@router.put("/groups/{slug}", response_model=GpoGroupOut)
def update_group(
    slug: str,
    body: GpoGroupCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    group = _get_group(db, slug)
    _require_admin(db, group.id, user)
    for key, val in body.model_dump(exclude_unset=True).items():
        if key != "slug":
            setattr(group, key, val)
    db.commit()
    db.refresh(group)
    return group


# ── Members ──

@router.post("/groups/{slug}/members", response_model=GpoMemberOut)
def add_member(
    slug: str,
    body: GpoMemberCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    group = _get_group(db, slug)
    member = GpoMember(
        gpo_group_id=group.id,
        **body.model_dump(),
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.get("/groups/{slug}/members", response_model=list[GpoMemberOut])
def list_members(slug: str, db: Session = Depends(get_db)):
    group = _get_group(db, slug)
    return db.query(GpoMember).filter(GpoMember.gpo_group_id == group.id).all()


@router.delete("/groups/{slug}/members/{member_id}")
def remove_member(
    slug: str,
    member_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    group = _get_group(db, slug)
    member = db.query(GpoMember).filter(
        GpoMember.id == member_id,
        GpoMember.gpo_group_id == group.id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return {"status": "removed"}


# ── Purchase Intents ──

@router.post("/groups/{slug}/intents", response_model=PurchaseIntentOut)
def submit_intent(
    slug: str,
    body: PurchaseIntentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    group = _get_group(db, slug)
    members = db.query(GpoMember).filter(GpoMember.gpo_group_id == group.id).all()
    if not members:
        raise HTTPException(status_code=403, detail="Not a member of this group")

    member = members[0]
    intent = GpoPurchaseIntent(
        gpo_member_id=member.id,
        cenabast_product_id=body.cenabast_product_id,
        product_name=body.product_name,
        quantity_units=body.quantity_units,
        target_month=body.target_month,
    )
    db.add(intent)
    db.commit()
    db.refresh(intent)
    return intent


@router.get("/groups/{slug}/intents", response_model=list[PurchaseIntentOut])
def list_intents(
    slug: str,
    month: str = Query(None),
    db: Session = Depends(get_db),
):
    group = _get_group(db, slug)
    member_ids = [m.id for m in db.query(GpoMember).filter(GpoMember.gpo_group_id == group.id).all()]
    q = db.query(GpoPurchaseIntent).filter(GpoPurchaseIntent.gpo_member_id.in_(member_ids))
    if month:
        q = q.filter(GpoPurchaseIntent.target_month == month)
    return q.order_by(GpoPurchaseIntent.created_at.desc()).all()


@router.delete("/groups/{slug}/intents/{intent_id}")
def cancel_intent(
    slug: str,
    intent_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    intent = db.query(GpoPurchaseIntent).filter(GpoPurchaseIntent.id == intent_id).first()
    if not intent or intent.status != IntentStatus.submitted:
        raise HTTPException(status_code=404, detail="Intent not found or already processed")
    intent.status = IntentStatus.cancelled
    db.commit()
    return {"status": "cancelled"}


# ── Aggregated Demand ──

@router.get("/groups/{slug}/demand")
def get_demand(
    slug: str,
    month: str = Query(...),
    db: Session = Depends(get_db),
):
    group = _get_group(db, slug)
    return get_aggregated_demand(db, str(group.id), month)


# ── Group Orders ──

@router.post("/groups/{slug}/orders", response_model=GroupOrderOut)
def create_order(
    slug: str,
    product_name: str = Query(...),
    target_month: str = Query(...),
    cenabast_product_id: str = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    group = _get_group(db, slug)
    _require_admin(db, group.id, user)
    order = create_group_order_from_demand(
        db, str(group.id), product_name, cenabast_product_id, target_month
    )
    if not order:
        raise HTTPException(status_code=400, detail="Could not create order from demand")
    return order


@router.get("/groups/{slug}/orders", response_model=list[GroupOrderOut])
def list_orders(slug: str, db: Session = Depends(get_db)):
    group = _get_group(db, slug)
    return db.query(GpoGroupOrder).filter(
        GpoGroupOrder.gpo_group_id == group.id
    ).order_by(GpoGroupOrder.created_at.desc()).all()


@router.get("/groups/{slug}/orders/{order_id}", response_model=GroupOrderOut)
def get_order(slug: str, order_id: str, db: Session = Depends(get_db)):
    group = _get_group(db, slug)
    order = db.query(GpoGroupOrder).filter(
        GpoGroupOrder.id == order_id,
        GpoGroupOrder.gpo_group_id == group.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put("/groups/{slug}/orders/{order_id}/status", response_model=GroupOrderOut)
def update_order_status(
    slug: str,
    order_id: str,
    body: GroupOrderStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    group = _get_group(db, slug)
    _require_admin(db, group.id, user)
    order = update_group_order_status(db, order_id, body.status)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/groups/{slug}/orders/{order_id}/allocations", response_model=list[AllocationOut])
def get_allocations(slug: str, order_id: str, db: Session = Depends(get_db)):
    return db.query(GpoAllocation).filter(GpoAllocation.group_order_id == order_id).all()


# ── Savings ──

@router.get("/groups/{slug}/savings")
def get_savings(slug: str, db: Session = Depends(get_db)):
    group = _get_group(db, slug)
    return get_group_savings(db, str(group.id))


# ── Facilitation Fees ──

@router.get("/facilitation-fees")
def list_fees(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(GpoFacilitationFee).order_by(GpoFacilitationFee.created_at.desc()).limit(100).all()
