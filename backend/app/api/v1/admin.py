from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User
from app.models.order import Order
from app.models.medication import Medication
from app.models.pharmacy import Pharmacy
from app.models.price import Price
from app.models.scrape_run import ScrapeRun

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def admin_stats(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_orders = db.query(func.count(Order.id)).scalar() or 0

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    orders_today = (
        db.query(func.count(Order.id))
        .filter(Order.created_at >= today_start)
        .scalar()
        or 0
    )

    total_revenue = (
        db.query(func.coalesce(func.sum(Order.total), 0))
        .filter(Order.status.in_(["confirmed", "delivering", "completed"]))
        .scalar()
    )

    paid_count = (
        db.query(func.count(Order.id))
        .filter(Order.status.in_(["confirmed", "delivering", "completed"]))
        .scalar()
        or 0
    )
    payment_success_rate = (
        round(paid_count / total_orders * 100, 1) if total_orders > 0 else 0
    )

    total_medications = db.query(func.count(Medication.id)).scalar() or 0
    total_pharmacies = db.query(func.count(Pharmacy.id)).scalar() or 0
    total_prices = db.query(func.count(Price.id)).scalar() or 0

    return {
        "total_users": total_users,
        "total_orders": total_orders,
        "orders_today": orders_today,
        "total_revenue": total_revenue,
        "payment_success_rate": payment_success_rate,
        "total_medications": total_medications,
        "total_pharmacies": total_pharmacies,
        "total_prices": total_prices,
    }


@router.get("/users")
def admin_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = (
        db.query(
            User.id,
            User.phone_number,
            User.name,
            User.created_at,
            User.is_admin,
            func.count(Order.id).label("order_count"),
            func.coalesce(func.sum(Order.total), 0).label("total_spent"),
        )
        .outerjoin(Order, Order.user_id == User.id)
        .group_by(User.id)
    )

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (User.phone_number.ilike(search_filter))
            | (User.name.ilike(search_filter))
        )

    total = query.count()
    rows = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

    users = [
        {
            "id": str(row.id),
            "phone_number": row.phone_number,
            "name": row.name,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "order_count": row.order_count,
            "total_spent": row.total_spent,
            "is_admin": row.is_admin,
        }
        for row in rows
    ]

    return {"users": users, "total": total, "limit": limit, "offset": offset}


@router.get("/users/{user_id}")
def admin_user_detail(
    user_id: UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    orders = (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .limit(20)
        .all()
    )

    return {
        "id": str(user.id),
        "phone_number": user.phone_number,
        "name": user.name,
        "comuna": user.comuna,
        "is_admin": user.is_admin,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "orders": [
            {
                "id": str(o.id),
                "status": o.status.value if o.status else None,
                "total": o.total,
                "payment_provider": o.payment_provider.value if o.payment_provider else None,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ],
    }
