import re
import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.models.medication import Medication
from app.models.price import Price
from app.models.pharmacy import Pharmacy
from app.schemas.medication import MedicationOut

router = APIRouter(prefix="/medications", tags=["medications"])

@router.get("/", response_model=list[MedicationOut])
def list_medications(db: Session = Depends(get_db)):
    return db.query(Medication).all()

@router.get("/search", response_model=list[MedicationOut])
def search_medications(
    q: str = Query(..., min_length=2),
    form: str | None = Query(None),
    requires_prescription: bool | None = Query(None),
    price_min: float | None = Query(None, ge=0),
    price_max: float | None = Query(None, ge=0),
    chain: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    # Clean Cenabast-style prefixes (e.g. "1-aciclovir" -> "aciclovir")
    clean_pattern = re.sub(r'^\d+-', '', q.strip())

    # Build text search conditions against both original and cleaned query
    text_conditions = [
        Medication.name.ilike(f"%{q}%"),
        Medication.active_ingredient.ilike(f"%{q}%"),
    ]
    if clean_pattern != q.strip():
        text_conditions.append(Medication.active_ingredient.ilike(f"%{clean_pattern}%"))

    # Determine if we need price/pharmacy joins
    needs_price_join = price_min is not None or price_max is not None or chain is not None

    if needs_price_join:
        query = db.query(Medication).join(Price, Price.medication_id == Medication.id)
        if chain is not None:
            query = query.join(Pharmacy, Pharmacy.id == Price.pharmacy_id).filter(
                Pharmacy.chain.ilike(f"%{chain}%")
            )
        if price_min is not None:
            query = query.filter(Price.price >= price_min)
        if price_max is not None:
            query = query.filter(Price.price <= price_max)
        query = query.distinct()
    else:
        query = db.query(Medication)

    query = query.filter(or_(*text_conditions))

    if form is not None:
        query = query.filter(Medication.form.ilike(f"%{form}%"))
    if requires_prescription is not None:
        query = query.filter(Medication.requires_prescription == requires_prescription)

    return query.offset(offset).limit(limit).all()


@router.get("/autocomplete")
def autocomplete_medications(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """Return top 8 medication name matches for search-as-you-type."""
    results = (
        db.query(Medication.name, Medication.slug, Medication.id)
        .filter(Medication.name.ilike(f"%{q}%"))
        .limit(8)
        .all()
    )
    return [
        {"name": r.name, "slug": r.slug, "id": str(r.id)}
        for r in results
    ]


@router.get("/{identifier}", response_model=MedicationOut)
def get_medication(identifier: str, db: Session = Depends(get_db)):
    """Fetch single medication by slug or UUID."""
    # Try UUID first
    try:
        med_uuid = _uuid.UUID(identifier)
        med = db.query(Medication).filter(Medication.id == med_uuid).first()
    except ValueError:
        # Not a valid UUID, treat as slug
        med = db.query(Medication).filter(Medication.slug == identifier).first()

    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    return med
