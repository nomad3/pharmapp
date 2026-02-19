from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint

def make_point(lng: float, lat: float):
    return func.ST_SetSRID(ST_MakePoint(lng, lat), 4326)

def nearby_query(db: Session, model, lat: float, lng: float, radius_km: float):
    user_point = make_point(lng, lat)
    distance = ST_Distance(model.location, func.cast(user_point, Geography)).label("distance_m")
    return (
        db.query(model, distance)
        .filter(ST_DWithin(model.location, func.cast(user_point, Geography), radius_km * 1000))
        .order_by(distance)
    )
