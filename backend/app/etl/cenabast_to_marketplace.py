"""
Sync Cenabast data into the PharmApp marketplace tables.

Creates Medication, Pharmacy, and Price records from the already-imported
cenabast_products and cenabast_invoices tables.

Usage:
    python -m app.etl.cenabast_to_marketplace
"""

import re
from collections import defaultdict
from sqlalchemy import func, distinct, text
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement

from app.core.database import SessionLocal, engine
from app.models import Base
from app.models.medication import Medication
from app.models.pharmacy import Pharmacy
from app.models.price import Price
from app.models.cenabast_product import CenabastProduct
from app.models.cenabast_invoice import CenabastInvoice


# ── Chilean region approximate center coordinates ──────────────────────
# Used as fallback when no specific address geocoding is available
REGION_COORDS = {
    "1": (-70.1357, -20.2133),   # Tarapacá
    "2": (-70.4000, -23.6500),   # Antofagasta
    "3": (-70.2500, -27.3668),   # Atacama
    "4": (-71.2500, -30.4000),   # Coquimbo
    "5": (-71.6167, -33.0458),   # Valparaíso
    "6": (-70.7333, -34.1708),   # O'Higgins
    "7": (-71.2500, -35.4264),   # Maule
    "8": (-73.0500, -36.8270),   # Biobío
    "9": (-72.6333, -38.7500),   # Araucanía
    "10": (-72.9333, -41.4689),  # Los Lagos
    "11": (-72.1000, -45.5750),  # Aysén
    "12": (-70.9167, -53.1500),  # Magallanes
    "13": (-70.6506, -33.4378),  # RM Santiago
    "14": (-73.2471, -39.8196),  # Los Ríos
    "15": (-70.3000, -18.4783),  # Arica y Parinacota
    "16": (-72.1033, -36.6066),  # Ñuble
}

# ── Parsing helpers ────────────────────────────────────────────────────

# Common pharmaceutical forms in Spanish
FORMS_MAP = {
    "CM REC": "comprimido recubierto",
    "CM": "comprimido",
    "CP": "cápsula",
    "CAP": "cápsula",
    "SOL INY": "solución inyectable",
    "S.INY": "solución inyectable",
    "P. LIOF": "polvo liofilizado",
    "SOL. INY": "solución inyectable",
    "SOL ORAL": "solución oral",
    "SUSP": "suspensión",
    "UNG": "ungüento",
    "CMA": "crema",
    "GEL": "gel",
    "JBE": "jarabe",
    "GOT": "gotas",
    "INH": "inhalador",
    "PARCHE": "parche",
    "SUP": "supositorio",
    "AMP": "ampolla",
    "FAM": "frasco ampolla",
    "FRA": "frasco",
    "DISP": "dispositivo",
    "CGE": "cartucho",
    "TU": "tubo",
}


def parse_product_name(name):
    """Parse a Cenabast product name into medication components.

    Examples:
        "JARDIANCE 25 MG CAJ 30 CM REC" → ("Jardiance", "25mg", "comprimido recubierto")
        "OMNITROPE 10 MG/1,5 ML SOL INY CGE 30 UI" → ("Omnitrope", "10mg/1.5ml", "solución inyectable")
    """
    if not name:
        return None, None, None

    # Extract dosage pattern (e.g., "25 MG", "10 MG/1,5 ML", "100 MCG")
    dosage_match = re.search(
        r'(\d+[\.,]?\d*)\s*(MG|MCG|G|ML|UI|UG)(?:/(\d+[\.,]?\d*)\s*(ML|MG|G))?',
        name, re.IGNORECASE
    )
    dosage = None
    if dosage_match:
        amt = dosage_match.group(1).replace(",", ".")
        unit = dosage_match.group(2).lower()
        dosage = f"{amt}{unit}"
        if dosage_match.group(3):
            amt2 = dosage_match.group(3).replace(",", ".")
            unit2 = dosage_match.group(4).lower()
            dosage += f"/{amt2}{unit2}"

    # Extract drug name (everything before the first number)
    name_match = re.match(r'^([A-Za-zÁÉÍÓÚÑáéíóúñ\s\-\.]+)', name)
    drug_name = name_match.group(1).strip().title() if name_match else name.split()[0].title()

    # Extract form
    form = None
    name_upper = name.upper()
    for key, value in FORMS_MAP.items():
        if key in name_upper:
            form = value
            break

    return drug_name, dosage, form


def sync_medications(db: Session) -> dict:
    """Create Medication records from CenabastProduct entries.

    Returns a mapping of codigo_producto → medication_id.
    """
    products = db.query(CenabastProduct).all()
    print(f"  Processing {len(products)} Cenabast products...")

    code_to_med_id = {}
    created = 0
    skipped = 0

    # Group by (drug_name, dosage) to avoid duplicates
    seen = {}  # (name_lower, dosage_lower) → medication_id

    for prod in products:
        drug_name, dosage, form = parse_product_name(prod.nombre_producto)
        if not drug_name:
            skipped += 1
            continue

        key = (drug_name.lower(), (dosage or "").lower())

        if key in seen:
            code_to_med_id[prod.codigo_producto] = seen[key]
            continue

        # Check if medication already exists
        existing = db.query(Medication).filter(
            func.lower(Medication.name) == f"{drug_name} {dosage or ''}".strip().lower()
        ).first()

        if existing:
            seen[key] = existing.id
            code_to_med_id[prod.codigo_producto] = existing.id
            skipped += 1
            continue

        med = Medication(
            name=f"{drug_name} {dosage or ''}".strip(),
            active_ingredient=prod.nombre_generico or drug_name,
            dosage=dosage,
            form=form,
            lab=prod.nombre_proveedor,
            requires_prescription=True,  # Cenabast products generally require prescription
        )
        db.add(med)
        db.flush()

        seen[key] = med.id
        code_to_med_id[prod.codigo_producto] = med.id
        created += 1

    print(f"  [OK] Medications: {created} created, {skipped} already existed/skipped")
    return code_to_med_id


def sync_pharmacies(db: Session) -> dict:
    """Create Pharmacy records from unique pharmacies in cenabast_invoices.

    Returns a mapping of rut → pharmacy_id.
    """
    # Get distinct pharmacies from invoices
    pharmacies = db.query(
        CenabastInvoice.rut_cliente_solicitante,
        func.max(CenabastInvoice.nombre_cliente_solicitante).label("nombre"),
        func.max(CenabastInvoice.direccion_solicitante).label("direccion"),
        func.max(CenabastInvoice.comuna_solicitante).label("comuna"),
        func.max(CenabastInvoice.region_solicitante).label("region"),
    ).filter(
        CenabastInvoice.rut_cliente_solicitante.isnot(None),
        CenabastInvoice.nombre_cliente_solicitante.isnot(None),
    ).group_by(
        CenabastInvoice.rut_cliente_solicitante
    ).all()

    print(f"  Processing {len(pharmacies)} unique pharmacies from invoices...")

    rut_to_pharm_id = {}
    created = 0
    skipped = 0

    for ph in pharmacies:
        if not ph.rut_cliente_solicitante or not ph.nombre:
            skipped += 1
            continue

        # Check if pharmacy already exists by name + comuna
        existing = db.query(Pharmacy).filter(
            func.lower(Pharmacy.name) == ph.nombre.strip().lower()
        ).first()

        if existing:
            rut_to_pharm_id[ph.rut_cliente_solicitante] = existing.id
            skipped += 1
            continue

        # Get coordinates from region
        region = str(ph.region).strip() if ph.region else "13"
        lng, lat = REGION_COORDS.get(region, (-70.6506, -33.4378))

        pharmacy = Pharmacy(
            chain="cenabast",
            name=ph.nombre.strip()[:200],
            address=ph.direccion.strip()[:200] if ph.direccion else f"Comuna {ph.comuna or 'N/A'}",
            comuna=ph.comuna.strip().title() if ph.comuna else "Santiago",
            location=WKTElement(f"POINT({lng} {lat})", srid=4326),
            phone=None,
        )
        db.add(pharmacy)
        db.flush()

        rut_to_pharm_id[ph.rut_cliente_solicitante] = pharmacy.id
        created += 1

    print(f"  [OK] Pharmacies: {created} created, {skipped} already existed/skipped")
    return rut_to_pharm_id


def sync_prices(db: Session, code_to_med_id: dict, rut_to_pharm_id: dict):
    """Create Price records from cenabast_invoices.

    Aggregates invoices by (product, pharmacy) to compute average prices,
    rather than creating one price per invoice (680K would be too many).
    """
    # Get average price per (product_code, pharmacy_rut) from recent invoices (last 12 months)
    price_data = db.query(
        CenabastInvoice.codigo_producto_comercial,
        CenabastInvoice.rut_cliente_solicitante,
        func.avg(
            CenabastInvoice.monto_bruto / func.nullif(CenabastInvoice.cantidad_unitaria, 0)
        ).label("avg_unit_price"),
        func.max(CenabastInvoice.cantidad_unitaria).label("has_stock"),
    ).filter(
        CenabastInvoice.codigo_producto_comercial.isnot(None),
        CenabastInvoice.rut_cliente_solicitante.isnot(None),
        CenabastInvoice.monto_bruto.isnot(None),
        CenabastInvoice.monto_bruto > 0,
        CenabastInvoice.cantidad_unitaria.isnot(None),
        CenabastInvoice.cantidad_unitaria > 0,
        CenabastInvoice.ano >= 2024,  # Recent data only
    ).group_by(
        CenabastInvoice.codigo_producto_comercial,
        CenabastInvoice.rut_cliente_solicitante,
    ).all()

    print(f"  Processing {len(price_data)} price aggregations...")

    # Delete existing cenabast-sourced prices (from pharmacies with chain='cenabast')
    cenabast_pharm_ids = list(rut_to_pharm_id.values())
    if cenabast_pharm_ids:
        db.query(Price).filter(Price.pharmacy_id.in_(cenabast_pharm_ids)).delete(
            synchronize_session=False
        )
        db.flush()

    batch = []
    created = 0
    skipped = 0

    for row in price_data:
        med_id = code_to_med_id.get(row.codigo_producto_comercial)
        pharm_id = rut_to_pharm_id.get(row.rut_cliente_solicitante)

        if not med_id or not pharm_id or not row.avg_unit_price:
            skipped += 1
            continue

        price_val = round(float(row.avg_unit_price), 0)
        if price_val <= 0:
            skipped += 1
            continue

        batch.append(Price(
            medication_id=med_id,
            pharmacy_id=pharm_id,
            price=price_val,
            in_stock=True,
            source_url="cenabast",
        ))
        created += 1

        if len(batch) >= 1000:
            db.bulk_save_objects(batch)
            db.flush()
            batch.clear()

    if batch:
        db.bulk_save_objects(batch)
        db.flush()

    print(f"  [OK] Prices: {created} created, {skipped} skipped")


def sync_all():
    """Sync all Cenabast data into the marketplace."""
    print("Creating tables if they do not exist...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("\n1/3 Syncing medications...")
        code_to_med_id = sync_medications(db)
        db.commit()

        print("\n2/3 Syncing pharmacies...")
        rut_to_pharm_id = sync_pharmacies(db)
        db.commit()

        print("\n3/3 Syncing prices...")
        sync_prices(db, code_to_med_id, rut_to_pharm_id)
        db.commit()

        # Print summary
        med_count = db.query(func.count(Medication.id)).scalar()
        pharm_count = db.query(func.count(Pharmacy.id)).scalar()
        price_count = db.query(func.count(Price.id)).scalar()
        print(f"\n--- Marketplace Summary ---")
        print(f"  Medications: {med_count}")
        print(f"  Pharmacies:  {pharm_count}")
        print(f"  Prices:      {price_count}")

    except Exception:
        db.rollback()
        print("\n[ERROR] Sync failed — rolled back.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    sync_all()
