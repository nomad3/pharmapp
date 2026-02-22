from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.order import Order
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

@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
