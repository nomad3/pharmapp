from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_Distance
from app.models.price import Price
from app.models.pharmacy import Pharmacy
from app.services.geolocation import make_point

def compare_prices(db: Session, medication_id: str, lat: float, lng: float, radius_km: float = 10.0):
    user_point = make_point(lng, lat)
    distance = ST_Distance(Pharmacy.location, func.cast(user_point, Geography)).label("distance_m")

    results = (
        db.query(Price, Pharmacy, distance)
        .join(Pharmacy, Price.pharmacy_id == Pharmacy.id)
        .filter(
            Price.medication_id == medication_id,
            Price.in_stock == True,
            ST_Distance(Pharmacy.location, func.cast(user_point, Geography)) <= radius_km * 1000,
        )
        .order_by(Price.price.asc())
        .all()
    )
    return results
