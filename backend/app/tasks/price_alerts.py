"""Scheduled job to check price alerts and notify users via WhatsApp."""
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.price_alert import PriceAlert
from app.models.price import Price
from app.models.medication import Medication
from app.models.pharmacy import Pharmacy
from app.models.user import User

logger = logging.getLogger(__name__)


async def check_price_alerts():
    """Check all active price alerts and send WhatsApp notifications for matches."""
    from app.core.database import SessionLocal
    from app.services import whatsapp

    db = SessionLocal()
    try:
        alerts = db.query(PriceAlert).filter(PriceAlert.is_active == True).all()
        if not alerts:
            logger.info("No active price alerts to check")
            return

        logger.info("Checking %d active price alerts...", len(alerts))
        notified = 0
        now = datetime.now(timezone.utc)
        cooldown = timedelta(hours=24)

        for alert in alerts:
            # Skip if notified recently
            if alert.last_notified_at and (now - alert.last_notified_at) < cooldown:
                continue

            # Find minimum price for this medication
            best = (
                db.query(Price, Pharmacy)
                .join(Pharmacy, Price.pharmacy_id == Pharmacy.id)
                .filter(
                    Price.medication_id == alert.medication_id,
                    Price.in_stock == True,
                    Price.price > 0,
                )
                .order_by(Price.price.asc())
                .first()
            )

            if not best:
                continue

            price_record, pharmacy = best

            if price_record.price <= alert.target_price:
                # Get medication name and user phone
                medication = db.query(Medication).filter(
                    Medication.id == alert.medication_id
                ).first()
                user = db.query(User).filter(User.id == alert.user_id).first()

                if not medication or not user:
                    continue

                try:
                    await whatsapp.send_price_alert(
                        user.phone_number,
                        medication.name,
                        pharmacy.name,
                        price_record.price,
                    )
                    alert.last_notified_at = now
                    notified += 1
                except Exception:
                    logger.exception(
                        "Failed to send price alert for user %s, med %s",
                        alert.user_id, alert.medication_id,
                    )

        db.commit()
        logger.info("Price alerts: checked %d, notified %d", len(alerts), notified)

    except Exception:
        logger.exception("Price alert check failed")
    finally:
        db.close()
