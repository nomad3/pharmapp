from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_premium_user
from app.models.user import User
from app.models.price_alert import PriceAlert
from app.models.medication import Medication
from app.schemas.premium import (
    PriceAlertCreate, PriceAlertOut,
    PriceHistoryItem, GenericAlternative,
    UserSubscriptionOut, PremiumCheckoutRequest,
)
from app.services import premium_service
from app.models.user_subscription import UserSubscription, UserTier

router = APIRouter(prefix="/premium", tags=["premium"])


@router.get("/status", response_model=UserSubscriptionOut)
def get_premium_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = db.query(UserSubscription).filter(UserSubscription.user_id == user.id).first()
    if not sub:
        return UserSubscriptionOut(tier="free")
    return UserSubscriptionOut(
        tier=sub.tier.value,
        current_period_end=str(sub.current_period_end) if sub.current_period_end else None,
    )


@router.post("/checkout")
def premium_checkout(
    body: PremiumCheckoutRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.core.config import settings
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Create or get Stripe customer
    sub = db.query(UserSubscription).filter(UserSubscription.user_id == user.id).first()

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": settings.STRIPE_PRICE_ID_PREMIUM, "quantity": 1}],
        success_url=(body.return_url or "http://localhost:3000") + "/premium?success=true",
        cancel_url=(body.return_url or "http://localhost:3000") + "/premium?canceled=true",
        metadata={"user_id": str(user.id), "type": "consumer_premium"},
    )
    return {"checkout_url": session.url}


@router.post("/alerts", response_model=PriceAlertOut)
def create_alert(
    body: PriceAlertCreate,
    user: User = Depends(require_premium_user),
    db: Session = Depends(get_db),
):
    med = db.query(Medication).filter(Medication.id == body.medication_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

    alert = PriceAlert(
        user_id=user.id,
        medication_id=body.medication_id,
        target_price=body.target_price,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    return PriceAlertOut(
        id=alert.id,
        medication_id=alert.medication_id,
        target_price=alert.target_price,
        is_active=alert.is_active,
        medication_name=med.name,
    )


@router.get("/alerts", response_model=list[PriceAlertOut])
def list_alerts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alerts = db.query(PriceAlert).filter(
        PriceAlert.user_id == user.id
    ).order_by(PriceAlert.created_at.desc()).all()

    results = []
    for a in alerts:
        med = db.query(Medication).filter(Medication.id == a.medication_id).first()
        results.append(PriceAlertOut(
            id=a.id,
            medication_id=a.medication_id,
            target_price=a.target_price,
            is_active=a.is_active,
            medication_name=med.name if med else None,
            last_notified_at=str(a.last_notified_at) if a.last_notified_at else None,
        ))
    return results


@router.delete("/alerts/{alert_id}")
def delete_alert(
    alert_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.query(PriceAlert).filter(
        PriceAlert.id == alert_id, PriceAlert.user_id == user.id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_active = False
    db.commit()
    return {"status": "deactivated"}


@router.get("/price-history/{medication_id}", response_model=list[PriceHistoryItem])
def price_history(
    medication_id: str,
    user: User = Depends(require_premium_user),
    db: Session = Depends(get_db),
):
    return premium_service.get_price_history(db, medication_id)


@router.get("/generics/{medication_id}", response_model=list[GenericAlternative])
def generic_alternatives(
    medication_id: str,
    user: User = Depends(require_premium_user),
    db: Session = Depends(get_db),
):
    return premium_service.get_generic_alternatives(db, medication_id)
