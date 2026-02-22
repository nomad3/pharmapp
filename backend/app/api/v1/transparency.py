from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.transparency_service import (
    get_cenabast_cost_for_medication,
    get_most_overpriced_medications,
    get_pharmacy_transparency_index,
    get_transparency_stats,
)

router = APIRouter(prefix="/transparency", tags=["transparency"])


@router.get("/most-overpriced")
def most_overpriced(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return get_most_overpriced_medications(db, limit=limit)


@router.get("/pharmacy-index")
def pharmacy_index(db: Session = Depends(get_db)):
    return get_pharmacy_transparency_index(db)


@router.get("/medication/{medication_id}/cenabast-cost")
def medication_cenabast_cost(
    medication_id: str,
    db: Session = Depends(get_db),
):
    result = get_cenabast_cost_for_medication(db, medication_id)
    if not result:
        return {"avg_cenabast_cost": None, "precio_maximo_publico": None, "invoice_count": 0}
    return result


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    return get_transparency_stats(db)
