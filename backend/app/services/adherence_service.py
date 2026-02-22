import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.adherence_program import AdherenceProgram
from app.models.adherence_discount_tier import AdherenceDiscountTier
from app.models.adherence_enrollment import AdherenceEnrollment, EnrollmentStatus
from app.models.adherence_refill import AdherenceRefill, RefillStatus
from app.models.adherence_sponsor import AdherenceSponsor
from app.models.adherence_sponsor_charge import AdherenceSponsorCharge, ChargeType
from app.models.pharmacy_discount_cap import PharmacyDiscountCap
from app.models.order_item import OrderItem

logger = logging.getLogger(__name__)


def enroll_user(db: Session, user_id: str, program_id: str, pharmacy_partner_id: str = None, whatsapp_consent: bool = True):
    existing = db.query(AdherenceEnrollment).filter(
        AdherenceEnrollment.user_id == user_id,
        AdherenceEnrollment.program_id == program_id,
        AdherenceEnrollment.status == EnrollmentStatus.active,
    ).first()
    if existing:
        return existing

    program = db.query(AdherenceProgram).filter(AdherenceProgram.id == program_id).first()
    if not program:
        return None

    now = datetime.now(timezone.utc)
    next_due = now + timedelta(days=program.refill_interval_days)

    enrollment = AdherenceEnrollment(
        user_id=user_id,
        program_id=program_id,
        pharmacy_partner_id=pharmacy_partner_id,
        whatsapp_consent=whatsapp_consent,
        next_refill_due=next_due,
    )
    db.add(enrollment)
    db.flush()

    first_refill = AdherenceRefill(
        enrollment_id=enrollment.id,
        due_date=next_due,
    )
    db.add(first_refill)

    # Charge sponsor for enrollment if applicable
    sponsor = db.query(AdherenceSponsor).filter(
        AdherenceSponsor.program_id == program_id
    ).first()
    if sponsor and sponsor.cost_per_enrollment > 0:
        charge = AdherenceSponsorCharge(
            sponsor_id=sponsor.id,
            charge_type=ChargeType.enrollment,
            amount=sponsor.cost_per_enrollment,
        )
        db.add(charge)
        sponsor.budget_remaining -= sponsor.cost_per_enrollment

    db.commit()
    db.refresh(enrollment)
    return enrollment


def record_refill(db: Session, enrollment_id: str, order_id: str):
    enrollment = db.query(AdherenceEnrollment).filter(
        AdherenceEnrollment.id == enrollment_id
    ).first()
    if not enrollment:
        return None

    program = db.query(AdherenceProgram).filter(
        AdherenceProgram.id == enrollment.program_id
    ).first()

    pending_refill = db.query(AdherenceRefill).filter(
        AdherenceRefill.enrollment_id == enrollment_id,
        AdherenceRefill.status == RefillStatus.pending,
    ).order_by(AdherenceRefill.due_date).first()

    now = datetime.now(timezone.utc)

    if pending_refill:
        pending_refill.order_id = order_id
        pending_refill.actual_date = now

        grace_end = pending_refill.due_date + timedelta(days=program.grace_period_days if program else 5)
        if now <= grace_end:
            pending_refill.status = RefillStatus.on_time
            enrollment.consecutive_on_time += 1
            enrollment.total_on_time += 1
        else:
            pending_refill.status = RefillStatus.late
            enrollment.consecutive_on_time = 0
            enrollment.total_late += 1

        discount_pct = get_current_discount(db, enrollment_id)
        pending_refill.discount_pct_applied = discount_pct

        enrollment.total_refills += 1
        refill = pending_refill
    else:
        refill = AdherenceRefill(
            enrollment_id=enrollment_id,
            order_id=order_id,
            due_date=now,
            actual_date=now,
            status=RefillStatus.on_time,
        )
        db.add(refill)
        enrollment.consecutive_on_time += 1
        enrollment.total_on_time += 1
        enrollment.total_refills += 1

    enrollment.adherence_score = calculate_adherence_score(enrollment)
    enrollment.current_discount_pct = get_current_discount(db, enrollment_id)

    if program:
        enrollment.next_refill_due = now + timedelta(days=program.refill_interval_days)
        next_refill = AdherenceRefill(
            enrollment_id=enrollment_id,
            due_date=enrollment.next_refill_due,
        )
        db.add(next_refill)

    # Sponsor charge for refill
    sponsor = db.query(AdherenceSponsor).filter(
        AdherenceSponsor.program_id == enrollment.program_id
    ).first()
    if sponsor and sponsor.cost_per_refill > 0:
        charge = AdherenceSponsorCharge(
            sponsor_id=sponsor.id,
            refill_id=refill.id,
            charge_type=ChargeType.refill,
            amount=sponsor.cost_per_refill,
        )
        db.add(charge)
        sponsor.budget_remaining -= sponsor.cost_per_refill

    db.commit()
    db.refresh(enrollment)
    return refill


def calculate_adherence_score(enrollment):
    total = enrollment.total_on_time + enrollment.total_late + enrollment.total_missed
    if total == 0:
        return 0
    return round((enrollment.total_on_time + 0.5 * enrollment.total_late) / total * 100, 1)


def get_current_discount(db: Session, enrollment_id: str):
    enrollment = db.query(AdherenceEnrollment).filter(
        AdherenceEnrollment.id == enrollment_id
    ).first()
    if not enrollment:
        return 0

    tier = db.query(AdherenceDiscountTier).filter(
        AdherenceDiscountTier.program_id == enrollment.program_id,
        AdherenceDiscountTier.min_consecutive_refills <= enrollment.consecutive_on_time,
    ).order_by(
        AdherenceDiscountTier.min_consecutive_refills.desc()
    ).first()

    if not tier:
        return 0

    discount = tier.discount_pct

    # Cap at program max
    program = db.query(AdherenceProgram).filter(
        AdherenceProgram.id == enrollment.program_id
    ).first()
    if program:
        discount = min(discount, program.max_discount_pct)

    # Cap at pharmacy partner max
    if enrollment.pharmacy_partner_id:
        cap = db.query(PharmacyDiscountCap).filter(
            PharmacyDiscountCap.pharmacy_partner_id == enrollment.pharmacy_partner_id,
            PharmacyDiscountCap.program_id == enrollment.program_id,
        ).first()
        if cap:
            discount = min(discount, cap.max_discount_pct)

    return discount


def apply_adherence_discount(db: Session, user_id: str, medication_id: str, base_price: float):
    enrollment = db.query(AdherenceEnrollment).join(
        AdherenceProgram, AdherenceEnrollment.program_id == AdherenceProgram.id
    ).filter(
        AdherenceEnrollment.user_id == user_id,
        AdherenceProgram.medication_id == medication_id,
        AdherenceEnrollment.status == EnrollmentStatus.active,
    ).first()

    if not enrollment:
        return {"discount_pct": 0, "discount_amount": 0, "final_price": base_price}

    discount_pct = get_current_discount(db, str(enrollment.id))
    discount_amount = round(base_price * discount_pct, 0)
    final_price = base_price - discount_amount

    return {
        "discount_pct": discount_pct,
        "discount_amount": discount_amount,
        "final_price": final_price,
        "enrollment_id": str(enrollment.id),
    }


def check_missed_refills(db: Session):
    now = datetime.now(timezone.utc)
    overdue = db.query(AdherenceRefill).join(
        AdherenceEnrollment, AdherenceRefill.enrollment_id == AdherenceEnrollment.id
    ).join(
        AdherenceProgram, AdherenceEnrollment.program_id == AdherenceProgram.id
    ).filter(
        AdherenceRefill.status == RefillStatus.pending,
        AdherenceRefill.due_date < now - timedelta(days=5),
    ).all()

    count = 0
    for refill in overdue:
        refill.status = RefillStatus.missed

        enrollment = db.query(AdherenceEnrollment).filter(
            AdherenceEnrollment.id == refill.enrollment_id
        ).first()
        if enrollment:
            enrollment.total_missed += 1
            enrollment.consecutive_on_time = 0
            enrollment.adherence_score = calculate_adherence_score(enrollment)
            enrollment.current_discount_pct = get_current_discount(db, str(enrollment.id))
        count += 1

    if count > 0:
        db.commit()
    return {"missed_count": count}


def get_user_adherence_dashboard(db: Session, user_id: str):
    enrollments = db.query(AdherenceEnrollment).filter(
        AdherenceEnrollment.user_id == user_id,
    ).all()

    enrollment_data = []
    total_savings = 0

    for e in enrollments:
        program = db.query(AdherenceProgram).filter(AdherenceProgram.id == e.program_id).first()

        refills = db.query(AdherenceRefill).filter(
            AdherenceRefill.enrollment_id == e.id,
            AdherenceRefill.status != RefillStatus.pending,
        ).all()

        savings = sum(r.discount_amount for r in refills if r.discount_amount)
        total_savings += savings

        enrollment_data.append({
            "enrollment_id": str(e.id),
            "program_name": program.name if program else None,
            "program_slug": program.slug if program else None,
            "medication_id": str(program.medication_id) if program else None,
            "status": e.status.value if hasattr(e.status, 'value') else e.status,
            "consecutive_on_time": e.consecutive_on_time,
            "adherence_score": e.adherence_score,
            "current_discount_pct": e.current_discount_pct,
            "next_refill_due": str(e.next_refill_due) if e.next_refill_due else None,
            "total_refills": e.total_refills,
            "total_savings": savings,
        })

    avg_score = sum(e["adherence_score"] for e in enrollment_data) / len(enrollment_data) if enrollment_data else 0

    return {
        "enrollments": enrollment_data,
        "total_savings": total_savings,
        "avg_adherence_score": round(avg_score, 1),
    }


def record_refill_from_order(db: Session, order):
    """Match a completed order to pending adherence refills."""
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    for item in items:
        enrollment = db.query(AdherenceEnrollment).join(
            AdherenceProgram, AdherenceEnrollment.program_id == AdherenceProgram.id
        ).filter(
            AdherenceEnrollment.user_id == order.user_id,
            AdherenceProgram.medication_id == item.medication_id,
            AdherenceEnrollment.status == EnrollmentStatus.active,
        ).first()

        if enrollment:
            record_refill(db, str(enrollment.id), str(order.id))
