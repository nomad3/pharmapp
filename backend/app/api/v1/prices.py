from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.price import PriceCompareItem
from app.schemas.pharmacy import PharmacyOut
from app.services.price_engine import compare_prices

router = APIRouter(prefix="/prices", tags=["prices"])

@router.get("/compare", response_model=list[PriceCompareItem])
def compare(
    medication_id: str = Query(...),
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(default=10.0),
    db: Session = Depends(get_db),
):
    results = compare_prices(db, medication_id, lat, lng, radius_km)
    items = []
    for price, pharmacy, distance_m in results:
        pharmacy_out = PharmacyOut.model_validate(pharmacy)
        pharmacy_out.distance_km = round(distance_m / 1000, 2)
        items.append(PriceCompareItem(
            price=price.price,
            in_stock=price.in_stock,
            pharmacy=pharmacy_out,
            distance_km=pharmacy_out.distance_km,
        ))
    return items
