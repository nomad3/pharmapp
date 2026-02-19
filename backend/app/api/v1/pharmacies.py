from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.pharmacy import Pharmacy
from app.schemas.pharmacy import PharmacyOut
from app.services.geolocation import nearby_query

router = APIRouter(prefix="/pharmacies", tags=["pharmacies"])

@router.get("/nearby", response_model=list[PharmacyOut])
def nearby_pharmacies(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(default=5.0),
    db: Session = Depends(get_db),
):
    results = nearby_query(db, Pharmacy, lat, lng, radius_km).limit(50).all()
    pharmacies = []
    for pharmacy, distance_m in results:
        out = PharmacyOut.model_validate(pharmacy)
        out.distance_km = round(distance_m / 1000, 2)
        pharmacies.append(out)
    return pharmacies
