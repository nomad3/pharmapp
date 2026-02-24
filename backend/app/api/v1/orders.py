import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.medication import Medication
from app.models.pharmacy import Pharmacy
from app.schemas.order import OrderCreate, OrderOut
from app.services.order_service import create_order
from app.services.referral_service import track_event
from app.models.referral_event import ReferralEventType
from app.services import whatsapp

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])

# Valid status transitions
VALID_TRANSITIONS = {
    OrderStatus.confirmed: [OrderStatus.delivering, OrderStatus.cancelled],
    OrderStatus.delivering: [OrderStatus.completed, OrderStatus.cancelled],
    OrderStatus.pending: [OrderStatus.cancelled],
    OrderStatus.payment_sent: [OrderStatus.cancelled],
}


class StatusUpdate(BaseModel):
    status: str


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


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: str,
    body: StatusUpdate,
    db: Session = Depends(get_db),
):
    """Update order status (admin endpoint). Validates transitions and sends WhatsApp notifications."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        new_status = OrderStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")

    allowed = VALID_TRANSITIONS.get(order.status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {order.status.value} to {new_status.value}",
        )

    order.status = new_status
    db.commit()

    # Send WhatsApp notification
    user = db.query(User).filter(User.id == order.user_id).first()
    if user:
        try:
            status_map = {
                "delivering": "dispatched",
                "completed": "delivered",
            }
            wa_status = status_map.get(new_status.value, new_status.value)
            await whatsapp.send_delivery_update(
                user.phone_number, str(order.id), wa_status
            )
        except Exception:
            logger.warning("Failed to send WhatsApp for order %s status update", order.id)

    return {
        "id": str(order.id),
        "status": order.status.value,
        "message": f"Order status updated to {new_status.value}",
    }


@router.get("/admin/all")
def list_all_orders(
    db: Session = Depends(get_db),
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """List all orders (admin). Optionally filter by status."""
    query = db.query(Order).order_by(Order.created_at.desc())
    if status:
        try:
            status_enum = OrderStatus(status)
            query = query.filter(Order.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    orders = query.limit(limit).all()
    return [
        {
            "id": str(o.id),
            "user_id": str(o.user_id),
            "pharmacy_id": str(o.pharmacy_id),
            "status": o.status.value if o.status else "pending",
            "payment_provider": o.payment_provider.value if o.payment_provider else None,
            "payment_status": o.payment_status,
            "total": o.total,
            "created_at": str(o.created_at),
        }
        for o in orders
    ]
