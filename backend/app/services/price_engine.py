from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_Distance
from app.models.price import Price
from app.models.pharmacy import Pharmacy
from app.services.geolocation import make_point


def compare_prices(db: Session, medication_id: str, lat: float, lng: float, radius_km: float = 10.0):
    """Compare prices across pharmacies, smartly grouped.

    Returns online chain prices (best per chain) + nearest Cenabast pharmacies.
    Avoids returning hundreds of identical-price Cenabast results.
    """
    user_point = make_point(lng, lat)
    distance = ST_Distance(Pharmacy.location, func.cast(user_point, Geography)).label("distance_m")

    # 1. Online chain pharmacies (scraped) — no distance filter, best price per chain
    online_results = (
        db.query(Price, Pharmacy, distance)
        .join(Pharmacy, Price.pharmacy_id == Pharmacy.id)
        .filter(
            Price.medication_id == medication_id,
            Price.in_stock == True,
            Pharmacy.address == "Venta online",
        )
        .order_by(Price.price.asc())
        .all()
    )

    # 2. Physical pharmacies (Cenabast + others) — within radius, sorted by distance
    physical_results = (
        db.query(Price, Pharmacy, distance)
        .join(Pharmacy, Price.pharmacy_id == Pharmacy.id)
        .filter(
            Price.medication_id == medication_id,
            Price.in_stock == True,
            Pharmacy.address != "Venta online",
            ST_Distance(Pharmacy.location, func.cast(user_point, Geography)) <= radius_km * 1000,
        )
        .order_by(distance.asc())
        .limit(20)
        .all()
    )

    # Combine: online first (sorted by price), then physical (sorted by distance)
    return online_results + physical_results
