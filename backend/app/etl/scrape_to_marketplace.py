"""Normalize scraped pharmacy products into the marketplace tables."""
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from geoalchemy2.elements import WKTElement

from app.models.medication import Medication
from app.models.pharmacy import Pharmacy
from app.models.price import Price
from app.scrapers.base import ScrapedProduct

logger = logging.getLogger(__name__)

CHAIN_COORDS = {
    "cruz_verde": (-70.6506, -33.4378),
    "salcobrand": (-70.6506, -33.4378),
    "ahumada": (-70.6506, -33.4378),
    "dr_simi": (-70.6506, -33.4378),
}

CHAIN_DISPLAY = {
    "cruz_verde": "Cruz Verde",
    "salcobrand": "Salcobrand",
    "ahumada": "Farmacias Ahumada",
    "dr_simi": "Dr. Simi",
}


def _get_or_create_medication(
    db: Session, p: ScrapedProduct, med_cache: dict, stats: dict
) -> Medication | None:
    """Find existing or create new Medication, handling slug collisions."""
    name_lower = p.name.strip().lower()
    med = Medication(
        name=p.name.strip(),
        active_ingredient=p.active_ingredient,
        dosage=p.dosage,
        form=p.form,
        lab=p.lab,
        requires_prescription=p.requires_prescription,
    )
    try:
        with db.begin_nested():
            db.add(med)
            db.flush()
        med_cache[name_lower] = med
        stats["medications_created"] += 1
        return med
    except IntegrityError:
        # Slug or unique constraint collision — find existing
        existing = db.query(Medication).filter(
            Medication.name == p.name.strip(),
        ).first()
        if existing:
            med_cache[name_lower] = existing
            return existing
        logger.warning("Skipping product with slug collision: %s", p.name)
        stats["skipped"] += 1
        return None


def upsert_scraped_products(db: Session, products: list[ScrapedProduct]) -> dict:
    """Normalize scraped products into Medication/Pharmacy/Price tables.

    Returns stats dict with counts of created/updated records.
    """
    stats = {
        "medications_created": 0,
        "pharmacies_created": 0,
        "prices_upserted": 0,
        "skipped": 0,
    }

    # 1. Ensure chain pharmacies exist
    chain_pharmacy_ids = {}
    for chain in {p.chain for p in products}:
        display = CHAIN_DISPLAY.get(chain, chain)
        pharmacy = db.query(Pharmacy).filter(
            Pharmacy.chain == chain,
            Pharmacy.name == f"{display} Online",
        ).first()
        if not pharmacy:
            lng, lat = CHAIN_COORDS.get(chain, (-70.6506, -33.4378))
            pharmacy = Pharmacy(
                chain=chain,
                name=f"{display} Online",
                address="Venta online",
                comuna="Santiago",
                location=WKTElement(f"POINT({lng} {lat})", srid=4326),
            )
            db.add(pharmacy)
            db.flush()
            stats["pharmacies_created"] += 1
        chain_pharmacy_ids[chain] = pharmacy.id

    # 2. Deduplicate by (chain, sku)
    seen = set()
    unique_products = []
    for p in products:
        key = (p.chain, p.sku)
        if key in seen or not p.sku:
            continue
        seen.add(key)
        unique_products.append(p)

    # 3. Build medication name cache
    med_cache = {}
    for med in db.query(Medication).all():
        med_cache[med.name.strip().lower()] = med

    # 4. Upsert each product
    now = datetime.now(timezone.utc)
    for p in unique_products:
        if p.price <= 0:
            stats["skipped"] += 1
            continue

        # Match or create medication
        name_lower = p.name.strip().lower()
        med = med_cache.get(name_lower)
        if not med:
            med = _get_or_create_medication(db, p, med_cache, stats)
            if not med:
                continue

        pharmacy_id = chain_pharmacy_ids[p.chain]

        # Upsert price
        existing_price = db.query(Price).filter(
            Price.medication_id == med.id,
            Price.pharmacy_id == pharmacy_id,
        ).first()

        if existing_price:
            existing_price.price = p.price
            existing_price.in_stock = p.in_stock
            existing_price.source_url = p.source_url
            existing_price.scraped_at = now
        else:
            db.add(Price(
                medication_id=med.id,
                pharmacy_id=pharmacy_id,
                price=p.price,
                in_stock=p.in_stock,
                source_url=p.source_url,
                scraped_at=now,
            ))
        stats["prices_upserted"] += 1

    db.commit()
    return stats
