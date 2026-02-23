"""Normalize scraped pharmacy locations into the marketplace tables."""
import logging

from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement

from app.models.pharmacy import Pharmacy
from app.scrapers.locations.base import ScrapedLocation

logger = logging.getLogger(__name__)


def upsert_scraped_locations(db: Session, locations: list[ScrapedLocation]) -> dict:
    """Upsert scraped physical pharmacy locations into Pharmacy table.

    Dedup key: (chain, branch_code). Updates existing records, creates new ones.
    Returns stats dict.
    """
    stats = {
        "pharmacies_created": 0,
        "pharmacies_updated": 0,
        "skipped": 0,
    }

    seen = set()

    for loc in locations:
        key = (loc.chain, loc.branch_code)
        if key in seen or not loc.branch_code:
            stats["skipped"] += 1
            continue
        seen.add(key)

        if not loc.lat or not loc.lng:
            stats["skipped"] += 1
            continue

        existing = db.query(Pharmacy).filter(
            Pharmacy.chain == loc.chain,
            Pharmacy.branch_code == loc.branch_code,
        ).first()

        point = WKTElement(f"POINT({loc.lng} {loc.lat})", srid=4326)

        if existing:
            existing.name = loc.name or existing.name
            existing.address = loc.address or existing.address
            existing.comuna = loc.comuna or existing.comuna
            existing.location = point
            existing.phone = loc.phone or existing.phone
            existing.hours = loc.hours or existing.hours
            existing.is_retail = True
            stats["pharmacies_updated"] += 1
        else:
            db.add(Pharmacy(
                chain=loc.chain,
                branch_code=loc.branch_code,
                name=loc.name or f"{loc.chain} {loc.branch_code}",
                address=loc.address or "",
                comuna=loc.comuna or "",
                location=point,
                phone=loc.phone or "",
                hours=loc.hours or "",
                is_retail=True,
            ))
            stats["pharmacies_created"] += 1

    db.commit()
    logger.info("Location upsert complete: %s", stats)
    return stats
