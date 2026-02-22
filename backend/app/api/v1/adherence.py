from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_org_member
from app.models.user import User
from app.models.adherence_program import AdherenceProgram
from app.models.adherence_discount_tier import AdherenceDiscountTier
from app.models.adherence_enrollment import AdherenceEnrollment
from app.models.adherence_refill import AdherenceRefill
from app.models.adherence_sponsor import AdherenceSponsor
from app.models.adherence_sponsor_charge import AdherenceSponsorCharge
from app.models.pharmacy_discount_cap import PharmacyDiscountCap
from app.schemas.adherence import (
    AdherenceProgramOut, DiscountTierOut,
    EnrollmentCreate, EnrollmentOut,
    ProgramCreateRequest, TierCreateRequest,
    SponsorAttachRequest, SponsorProgramOut,
    SponsorChargeOut, DiscountCapUpdate,
)
from app.services.adherence_service import (
    enroll_user,
    get_user_adherence_dashboard,
    check_missed_refills,
    apply_adherence_discount,
)
from app.services.adherence_reminder_service import send_refill_reminders

router = APIRouter(prefix="/adherence", tags=["adherence"])


# ── Patient Endpoints ──

@router.get("/programs", response_model=list[AdherenceProgramOut])
def list_programs(db: Session = Depends(get_db)):
    return db.query(AdherenceProgram).order_by(AdherenceProgram.name).all()


@router.get("/programs/{slug}")
def get_program(slug: str, db: Session = Depends(get_db)):
    program = db.query(AdherenceProgram).filter(AdherenceProgram.slug == slug).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    tiers = db.query(AdherenceDiscountTier).filter(
        AdherenceDiscountTier.program_id == program.id
    ).order_by(AdherenceDiscountTier.min_consecutive_refills).all()

    return {
        "program": AdherenceProgramOut.model_validate(program).model_dump(),
        "tiers": [DiscountTierOut.model_validate(t).model_dump() for t in tiers],
    }


@router.post("/enroll", response_model=EnrollmentOut)
def enroll(
    body: EnrollmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    enrollment = enroll_user(
        db,
        user_id=str(user.id),
        program_id=body.program_id,
        pharmacy_partner_id=body.pharmacy_partner_id,
        whatsapp_consent=body.whatsapp_consent,
    )
    if not enrollment:
        raise HTTPException(status_code=400, detail="Could not enroll")
    return enrollment


@router.get("/enrollments", response_model=list[EnrollmentOut])
def my_enrollments(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(AdherenceEnrollment).filter(
        AdherenceEnrollment.user_id == user.id
    ).order_by(AdherenceEnrollment.created_at.desc()).all()


@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_user_adherence_dashboard(db, str(user.id))


@router.get("/savings")
def savings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    dash = get_user_adherence_dashboard(db, str(user.id))
    return {
        "total_savings": dash["total_savings"],
        "enrollment_count": len(dash["enrollments"]),
        "per_program": [
            {"program": e["program_name"], "savings": e["total_savings"]}
            for e in dash["enrollments"]
        ],
    }


@router.get("/enrollment/{enrollment_id}/refills")
def get_refills(
    enrollment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    enrollment = db.query(AdherenceEnrollment).filter(
        AdherenceEnrollment.id == enrollment_id,
        AdherenceEnrollment.user_id == user.id,
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    refills = db.query(AdherenceRefill).filter(
        AdherenceRefill.enrollment_id == enrollment_id
    ).order_by(AdherenceRefill.due_date.desc()).all()

    return refills


# ── Pharmacy Partner Endpoints ──

@router.get("/partner/stats")
def partner_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.models.pharmacy_partner import PharmacyPartner
    partner = db.query(PharmacyPartner).first()
    if not partner:
        return {"program_count": 0, "total_enrollments": 0, "avg_adherence_score": 0}

    from sqlalchemy import func
    enrollments = db.query(
        func.count(AdherenceEnrollment.id).label("total"),
        func.avg(AdherenceEnrollment.adherence_score).label("avg_score"),
    ).filter(
        AdherenceEnrollment.pharmacy_partner_id == partner.id,
    ).first()

    caps = db.query(func.count(PharmacyDiscountCap.id)).filter(
        PharmacyDiscountCap.pharmacy_partner_id == partner.id
    ).scalar()

    return {
        "program_count": caps or 0,
        "total_enrollments": int(enrollments.total or 0),
        "avg_adherence_score": round(float(enrollments.avg_score or 0), 1),
    }


@router.put("/partner/discount-cap")
def set_discount_cap(
    body: DiscountCapUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.models.pharmacy_partner import PharmacyPartner
    partner = db.query(PharmacyPartner).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Not a pharmacy partner")

    cap = db.query(PharmacyDiscountCap).filter(
        PharmacyDiscountCap.pharmacy_partner_id == partner.id,
        PharmacyDiscountCap.program_id == body.program_id,
    ).first()

    if cap:
        cap.max_discount_pct = body.max_discount_pct
    else:
        cap = PharmacyDiscountCap(
            pharmacy_partner_id=partner.id,
            program_id=body.program_id,
            max_discount_pct=body.max_discount_pct,
        )
        db.add(cap)

    db.commit()
    return {"status": "updated"}


# ── Sponsor Endpoints ──

@router.get("/sponsor/programs", response_model=list[SponsorProgramOut])
def sponsor_programs(
    db: Session = Depends(get_db),
    ctx=Depends(get_current_org_member),
):
    return db.query(AdherenceSponsor).filter(
        AdherenceSponsor.org_id == ctx["org_id"]
    ).all()


@router.get("/sponsor/programs/{program_id}/metrics")
def sponsor_metrics(
    program_id: str,
    db: Session = Depends(get_db),
    ctx=Depends(get_current_org_member),
):
    from sqlalchemy import func

    sponsor = db.query(AdherenceSponsor).filter(
        AdherenceSponsor.program_id == program_id,
        AdherenceSponsor.org_id == ctx["org_id"],
    ).first()
    if not sponsor:
        raise HTTPException(status_code=404, detail="Not sponsoring this program")

    total_enrollments = db.query(func.count(AdherenceEnrollment.id)).filter(
        AdherenceEnrollment.program_id == program_id
    ).scalar()

    avg_score = db.query(func.avg(AdherenceEnrollment.adherence_score)).filter(
        AdherenceEnrollment.program_id == program_id
    ).scalar()

    total_charges = db.query(func.sum(AdherenceSponsorCharge.amount)).filter(
        AdherenceSponsorCharge.sponsor_id == sponsor.id
    ).scalar()

    return {
        "total_enrollments": total_enrollments or 0,
        "avg_adherence_score": round(float(avg_score or 0), 1),
        "total_charges": float(total_charges or 0),
        "budget_remaining": sponsor.budget_remaining,
    }


@router.get("/sponsor/charges", response_model=list[SponsorChargeOut])
def sponsor_charges(
    db: Session = Depends(get_db),
    ctx=Depends(get_current_org_member),
):
    sponsors = db.query(AdherenceSponsor).filter(
        AdherenceSponsor.org_id == ctx["org_id"]
    ).all()
    sponsor_ids = [s.id for s in sponsors]
    if not sponsor_ids:
        return []

    return db.query(AdherenceSponsorCharge).filter(
        AdherenceSponsorCharge.sponsor_id.in_(sponsor_ids)
    ).order_by(AdherenceSponsorCharge.created_at.desc()).limit(200).all()


# ── Admin Endpoints ──

@router.post("/admin/programs", response_model=AdherenceProgramOut)
def create_program(
    body: ProgramCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    program = AdherenceProgram(**body.model_dump())
    db.add(program)
    db.commit()
    db.refresh(program)
    return program


@router.post("/admin/programs/{program_id}/tiers", response_model=DiscountTierOut)
def add_tier(
    program_id: str,
    body: TierCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tier = AdherenceDiscountTier(
        program_id=program_id,
        **body.model_dump(),
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


@router.post("/admin/programs/{program_id}/sponsor", response_model=SponsorProgramOut)
def attach_sponsor(
    program_id: str,
    body: SponsorAttachRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sponsor = AdherenceSponsor(
        program_id=program_id,
        org_id=body.org_id,
        budget_total=body.budget_total,
        budget_remaining=body.budget_total,
        cost_per_enrollment=body.cost_per_enrollment,
        cost_per_refill=body.cost_per_refill,
        discount_coverage_pct=body.discount_coverage_pct,
    )
    db.add(sponsor)
    db.commit()
    db.refresh(sponsor)
    return sponsor


@router.post("/admin/check-reminders")
async def trigger_reminders(db: Session = Depends(get_db)):
    return await send_refill_reminders(db)


@router.post("/admin/check-missed")
def trigger_missed(db: Session = Depends(get_db)):
    return check_missed_refills(db)
