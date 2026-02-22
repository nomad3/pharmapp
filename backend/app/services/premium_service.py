import logging
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.price import Price
from app.models.medication import Medication
from app.models.pharmacy import Pharmacy
from app.models.price_alert import PriceAlert
from app.models.user import User

logger = logging.getLogger(__name__)


def get_price_history(db: Session, medication_id: str, limit: int = 100):
    rows = db.query(
        Price.scraped_at,
        Price.price,
        Pharmacy.chain,
    ).join(Pharmacy, Price.pharmacy_id == Pharmacy.id).filter(
        Price.medication_id == medication_id,
        Price.scraped_at.isnot(None),
    ).order_by(Price.scraped_at.desc()).limit(limit).all()

    return [
        {
            "date": str(r.scraped_at)[:10] if r.scraped_at else "",
            "price": float(r.price),
            "pharmacy_chain": r.chain,
        }
        for r in rows
    ]


def get_generic_alternatives(db: Session, medication_id: str):
    med = db.query(Medication).filter(Medication.id == medication_id).first()
    if not med or not med.active_ingredient:
        return []

    alternatives = db.query(Medication).filter(
        Medication.active_ingredient == med.active_ingredient,
        Medication.id != medication_id,
    ).all()

    results = []
    for alt in alternatives:
        min_price = db.query(func.min(Price.price)).filter(
            Price.medication_id == alt.id,
            Price.in_stock == True,
        ).scalar()
        results.append({
            "id": alt.id,
            "name": alt.name,
            "active_ingredient": alt.active_ingredient,
            "lab": alt.lab,
            "min_price": float(min_price) if min_price else None,
        })

    results.sort(key=lambda x: x["min_price"] or float("inf"))
    return results


def check_price_alerts(db: Session):
    """Check all active alerts and return list of triggered ones. Call periodically."""
    alerts = db.query(PriceAlert).filter(PriceAlert.is_active == True).all()
    triggered = []

    for alert in alerts:
        current_min = db.query(func.min(Price.price)).filter(
            Price.medication_id == alert.medication_id,
            Price.in_stock == True,
        ).scalar()

        if current_min is not None and current_min <= alert.target_price:
            user = db.query(User).filter(User.id == alert.user_id).first()
            med = db.query(Medication).filter(Medication.id == alert.medication_id).first()

            triggered.append({
                "alert_id": alert.id,
                "user_phone": user.phone_number if user else None,
                "medication_name": med.name if med else None,
                "target_price": alert.target_price,
                "current_price": float(current_min),
            })

            alert.last_notified_at = datetime.now(timezone.utc)

    if triggered:
        db.commit()

    return triggered
