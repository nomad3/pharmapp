from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.medication import Medication
from app.models.pharmacy import Pharmacy
from app.schemas.order import OrderCreate, OrderOut
from app.services.order_service import create_order
from app.services.referral_service import track_event
from app.models.referral_event import ReferralEventType

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderOut)
async def create(
    body: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = await create_order(db, str(user.id), user.phone_number, body)

    track_event(
        db,
        ReferralEventType.order_created,
        user_id=str(user.id),
        pharmacy_id=str(body.pharmacy_id),
        order_id=str(order.id),
    )

    return order


@router.get("/")
def list_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
):
    """List current user's orders, most recent first."""
    orders = (
        db.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(o.id),
            "status": o.status.value if o.status else "pending",
            "payment_provider": o.payment_provider.value if o.payment_provider else None,
            "payment_url": o.payment_url,
            "total": o.total,
            "created_at": str(o.created_at),
        }
        for o in orders
    ]


@router.get("/{order_id}")
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get order with full details including items, pharmacy, and medication names."""
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    pharmacy = db.query(Pharmacy).filter(Pharmacy.id == order.pharmacy_id).first()

    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    items_out = []
    for item in items:
        med = db.query(Medication).filter(Medication.id == item.medication_id).first()
        items_out.append({
            "medication_id": str(item.medication_id),
            "medication_name": med.name if med else "Unknown",
            "quantity": item.quantity,
            "subtotal": item.subtotal,
        })

    return {
        "id": str(order.id),
        "status": order.status.value if order.status else "pending",
        "payment_provider": order.payment_provider.value if order.payment_provider else None,
        "payment_url": order.payment_url,
        "payment_status": order.payment_status,
        "total": order.total,
        "created_at": str(order.created_at),
        "pharmacy": {
            "id": str(pharmacy.id),
            "name": pharmacy.name,
            "chain": pharmacy.chain,
            "address": pharmacy.address,
        } if pharmacy else None,
        "items": items_out,
    }
