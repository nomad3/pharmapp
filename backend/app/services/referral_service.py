import logging
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.referral_event import ReferralEvent, ReferralEventType

logger = logging.getLogger(__name__)


def track_event(
    db: Session,
    event_type: ReferralEventType,
    user_id: str = None,
    session_id: str = None,
    medication_id: str = None,
    pharmacy_id: str = None,
    order_id: str = None,
):
    try:
        event = ReferralEvent(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            medication_id=medication_id,
            pharmacy_id=pharmacy_id,
            order_id=order_id,
        )
        db.add(event)
        db.commit()
    except Exception:
        logger.exception("Failed to track referral event")
        db.rollback()


def get_conversion_funnel(db: Session, start_date=None, end_date=None):
    q = db.query(
        ReferralEvent.event_type,
        func.count(ReferralEvent.id).label("count"),
        func.count(func.distinct(ReferralEvent.user_id)).label("unique_users"),
    ).group_by(ReferralEvent.event_type)

    if start_date:
        q = q.filter(ReferralEvent.created_at >= start_date)
    if end_date:
        q = q.filter(ReferralEvent.created_at <= end_date)

    results = {}
    for row in q.all():
        results[row.event_type.value] = {
            "count": int(row.count),
            "unique_users": int(row.unique_users),
        }
    return results
