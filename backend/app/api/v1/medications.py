from fastapi import APIRouter, Depends, Query
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
