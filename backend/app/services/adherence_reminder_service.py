import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.adherence_enrollment import AdherenceEnrollment, EnrollmentStatus
from app.models.adherence_refill import AdherenceRefill, RefillStatus
from app.models.adherence_program import AdherenceProgram
from app.models.user import User
from app.services import whatsapp

logger = logging.getLogger(__name__)


async def send_refill_reminders(db: Session):
    now = datetime.now(timezone.utc)
    reminder_window = now + timedelta(days=3)

    pending = db.query(AdherenceRefill, AdherenceEnrollment).join(
        AdherenceEnrollment, AdherenceRefill.enrollment_id == AdherenceEnrollment.id
    ).filter(
        AdherenceRefill.status == RefillStatus.pending,
        AdherenceRefill.due_date <= reminder_window,
        AdherenceRefill.due_date > now,
        AdherenceRefill.reminder_sent_at.is_(None),
        AdherenceEnrollment.status == EnrollmentStatus.active,
        AdherenceEnrollment.whatsapp_consent == True,
    ).all()

    count = 0
    for refill, enrollment in pending:
        user = db.query(User).filter(User.id == enrollment.user_id).first()
        program = db.query(AdherenceProgram).filter(AdherenceProgram.id == enrollment.program_id).first()

        if not user or not program:
            continue

        days_until = (refill.due_date.replace(tzinfo=timezone.utc) - now).days

        try:
            await whatsapp.send_refill_reminder(
                user.phone_number,
                program.name,
                days_until,
                enrollment.current_discount_pct,
            )
            refill.reminder_sent_at = now
            count += 1
        except Exception:
            logger.exception("Failed to send reminder to %s", user.phone_number)

    if count > 0:
        db.commit()
    return {"reminders_sent": count}


async def send_refill_confirmation(db: Session, refill_id: str):
    refill = db.query(AdherenceRefill).filter(AdherenceRefill.id == refill_id).first()
    if not refill:
        return

    enrollment = db.query(AdherenceEnrollment).filter(
        AdherenceEnrollment.id == refill.enrollment_id
    ).first()
    if not enrollment:
        return

    user = db.query(User).filter(User.id == enrollment.user_id).first()
    program = db.query(AdherenceProgram).filter(AdherenceProgram.id == enrollment.program_id).first()

    if not user or not program:
        return

    try:
        await whatsapp.send_refill_completed(
            user.phone_number,
            program.name,
            enrollment.current_discount_pct,
            refill.discount_amount or 0,
            enrollment.consecutive_on_time,
            str(enrollment.next_refill_due.date()) if enrollment.next_refill_due else None,
        )
    except Exception:
        logger.exception("Failed to send refill confirmation")


async def send_missed_refill_warning(db: Session, enrollment_id: str):
    enrollment = db.query(AdherenceEnrollment).filter(
        AdherenceEnrollment.id == enrollment_id
    ).first()
    if not enrollment:
        return

    user = db.query(User).filter(User.id == enrollment.user_id).first()
    program = db.query(AdherenceProgram).filter(AdherenceProgram.id == enrollment.program_id).first()

    if not user or not program:
        return

    try:
        await whatsapp.send_streak_broken(
            user.phone_number,
            program.name,
            enrollment.current_discount_pct,
        )
    except Exception:
        logger.exception("Failed to send missed refill warning")
