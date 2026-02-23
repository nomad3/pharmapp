"""Geocode Cenabast pharmacies using their addresses via Nominatim (OpenStreetMap).

Usage:
    python -m app.etl.geocode_pharmacies
"""
import asyncio
import logging
import re

import httpx
from sqlalchemy import text

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
RATE_LIMIT = 1.1  # Nominatim requires max 1 req/sec


def clean_address(address: str, comuna: str) -> str:
    """Build a geocodable address string from Cenabast data."""
    # Remove LOC/LOCAL references, unit numbers
    addr = re.sub(r',?\s*LOC\.?\s*\d+[A-Z]?', '', address, flags=re.IGNORECASE)
    addr = re.sub(r',?\s*LOCAL\s*\d+', '', addr, flags=re.IGNORECASE)
    addr = re.sub(r',?\s*PISO\s*\d+', '', addr, flags=re.IGNORECASE)
    addr = re.sub(r',?\s*OF\.?\s*\d+', '', addr, flags=re.IGNORECASE)
    addr = re.sub(r'\s+', ' ', addr).strip().rstrip(',').strip()
    return f"{addr}, {comuna}, Chile"


async def geocode_address(client: httpx.AsyncClient, address: str) -> tuple[float, float] | None:
    """Geocode a single address using Nominatim. Returns (lng, lat) or None."""
    try:
        resp = await client.get(NOMINATIM_URL, params={
            "q": address,
            "format": "json",
            "limit": 1,
            "countrycodes": "cl",
        })
        resp.raise_for_status()
        results = resp.json()
        if results:
            lat = float(results[0]["lat"])
            lng = float(results[0]["lon"])
            return (lng, lat)
    except Exception as e:
        logger.warning("Geocode failed for '%s': %s", address, e)
    return None


async def geocode_all():
    """Geocode all Cenabast pharmacies that still have region-level coordinates."""
    db = SessionLocal()
    try:
        # Find pharmacies with region-level coords (duplicated coords = not geocoded)
        rows = db.execute(text("""
            SELECT id, name, address, comuna,
                   ST_X(location::geometry) as lng, ST_Y(location::geometry) as lat
            FROM pharmacies
            WHERE chain = 'cenabast'
            ORDER BY name
        """)).fetchall()

        # Count how many share each coordinate (region-level ones have many duplicates)
        coord_counts = {}
        for r in rows:
            key = (round(r.lng, 4), round(r.lat, 4))
            coord_counts[key] = coord_counts.get(key, 0) + 1

        # Only geocode pharmacies with shared coords (region-level, not already geocoded)
        to_geocode = [r for r in rows if coord_counts.get((round(r.lng, 4), round(r.lat, 4)), 0) > 1]

        print(f"Found {len(to_geocode)} pharmacies with region-level coordinates to geocode")
        if not to_geocode:
            print("Nothing to geocode.")
            return

        updated = 0
        failed = 0

        async with httpx.AsyncClient(
            timeout=15,
            headers={"User-Agent": "PharmApp/1.0 (pharmacy geocoding)"},
        ) as client:
            for i, row in enumerate(to_geocode):
                address_str = clean_address(row.address, row.comuna)
                coords = await geocode_address(client, address_str)

                if coords:
                    lng, lat = coords
                    db.execute(text(
                        "UPDATE pharmacies SET location = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326) WHERE id = :id"
                    ), {"lng": lng, "lat": lat, "id": str(row.id)})
                    updated += 1
                    if updated % 50 == 0:
                        db.commit()
                        print(f"  [{i+1}/{len(to_geocode)}] Updated {updated} pharmacies...")
                else:
                    failed += 1

                if i < len(to_geocode) - 1:
                    await asyncio.sleep(RATE_LIMIT)

        db.commit()
        print(f"\nDone: {updated} geocoded, {failed} failed out of {len(to_geocode)}")

    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(geocode_all())
