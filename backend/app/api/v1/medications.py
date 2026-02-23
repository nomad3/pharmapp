import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.medication import Medication
from app.schemas.medication import MedicationOut

router = APIRouter(prefix="/medications", tags=["medications"])

@router.get("/", response_model=list[MedicationOut])
def list_medications(db: Session = Depends(get_db)):
    return db.query(Medication).all()

@router.get("/search", response_model=list[MedicationOut])
def search_medications(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    return (
        db.query(Medication)
        .filter(
            Medication.name.ilike(f"%{q}%")
            | Medication.active_ingredient.ilike(f"%{q}%")
        )
        .limit(50)
        .all()
    )

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
