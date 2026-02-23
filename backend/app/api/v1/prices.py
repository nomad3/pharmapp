from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.price import PriceCompareItem
from app.schemas.pharmacy import PharmacyOut
from app.services.price_engine import compare_prices
from app.services.transparency_service import get_cenabast_cost_for_medication
from app.services.referral_service import track_event
from app.models.referral_event import ReferralEventType

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
        is_online = pharmacy.address == "Venta online"
        pharmacy_out.distance_km = None if is_online else round(distance_m / 1000, 2)
        items.append(PriceCompareItem(
            price=price.price,
            in_stock=price.in_stock,
            pharmacy=pharmacy_out,
            distance_km=pharmacy_out.distance_km,
        ))

    track_event(db, ReferralEventType.view_prices, medication_id=medication_id)

    return items


@router.get("/compare-transparent")
def compare_transparent(
    medication_id: str = Query(...),
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(default=10.0),
    db: Session = Depends(get_db),
):
    results = compare_prices(db, medication_id, lat, lng, radius_km)
    cenabast = get_cenabast_cost_for_medication(db, medication_id)
    cenabast_cost = cenabast["avg_cenabast_cost"] if cenabast else None

    items = []
    for price, pharmacy, distance_m in results:
        pharmacy_out = PharmacyOut.model_validate(pharmacy)
        is_online = pharmacy.address == "Venta online"
        pharmacy_out.distance_km = None if is_online else round(distance_m / 1000, 2)

        markup_pct = None
        is_precio_justo = None
        if cenabast_cost and cenabast_cost > 0:
            markup_pct = round((price.price - cenabast_cost) / cenabast_cost * 100, 1)
            is_precio_justo = markup_pct <= 100

        items.append({
            "price": price.price,
            "in_stock": price.in_stock,
            "pharmacy": pharmacy_out.model_dump(),
            "distance_km": pharmacy_out.distance_km,
            "is_online": is_online,
            "cenabast_cost": cenabast_cost,
            "markup_pct": markup_pct,
            "is_precio_justo": is_precio_justo,
        })

    track_event(db, ReferralEventType.view_prices, medication_id=medication_id)

    return items
