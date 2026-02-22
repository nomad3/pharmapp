import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, cast, String
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.commission import Commission, CommissionStatus
from app.models.pharmacy_partner import PharmacyPartner
from app.models.pharmacy import Pharmacy
from app.schemas.commission import CommissionOut, CommissionSummary

router = APIRouter(prefix="/commissions", tags=["commissions"])


@router.get("/summary", response_model=list[CommissionSummary])
def commission_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    month_trunc = func.date_trunc("month", Commission.created_at)
    q = db.query(
        Commission.pharmacy_partner_id,
        cast(month_trunc, String).label("month"),
        func.count(Commission.id).label("total_orders"),
        func.sum(Commission.order_total).label("total_order_amount"),
        func.sum(Commission.commission_amount).label("total_commission"),
    ).group_by(Commission.pharmacy_partner_id, month_trunc).order_by(month_trunc.desc())

    results = []
    for row in q.all():
        partner = db.query(PharmacyPartner).filter(PharmacyPartner.id == row.pharmacy_partner_id).first()
        pharmacy = db.query(Pharmacy).filter(Pharmacy.id == partner.pharmacy_id).first() if partner else None
        results.append(CommissionSummary(
            pharmacy_name=pharmacy.name if pharmacy else None,
            month=row.month[:7] if row.month else "",
            total_orders=int(row.total_orders or 0),
            total_order_amount=float(row.total_order_amount or 0),
            total_commission=float(row.total_commission or 0),
        ))
    return results


@router.get("/", response_model=list[CommissionOut])
def list_commissions(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Commission).order_by(Commission.created_at.desc())

    if status:
        q = q.filter(Commission.status == status)

    commissions = q.limit(limit).all()
    return [
        CommissionOut(
            id=c.id,
            order_id=c.order_id,
            pharmacy_partner_id=c.pharmacy_partner_id,
            order_total=c.order_total,
            commission_rate=c.commission_rate,
            commission_amount=c.commission_amount,
            status=c.status.value,
            created_at=str(c.created_at) if c.created_at else None,
        )
        for c in commissions
    ]


@router.get("/export")
def export_commissions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    commissions = db.query(Commission).order_by(Commission.created_at.desc()).all()

    if not commissions:
        return {"error": "No commissions found"}

    rows = []
    for c in commissions:
        partner = db.query(PharmacyPartner).filter(PharmacyPartner.id == c.pharmacy_partner_id).first()
        pharmacy = db.query(Pharmacy).filter(Pharmacy.id == partner.pharmacy_id).first() if partner else None
        rows.append({
            "date": str(c.created_at)[:10] if c.created_at else "",
            "pharmacy": pharmacy.name if pharmacy else "",
            "order_total": c.order_total,
            "commission_rate": c.commission_rate,
            "commission_amount": c.commission_amount,
            "status": c.status.value,
        })

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=commissions.csv"},
    )
