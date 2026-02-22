from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cenabast_product import CenabastProduct
from app.models.medication import Medication
from app.models.pharmacy import Pharmacy
from app.models.price import Price


def _build_cost_map(db: Session):
    """Pre-compute avg precio_maximo_publico grouped by lowercase nombre_generico from CenabastProduct (1,245 records)."""
    rows = db.query(
        func.lower(CenabastProduct.nombre_generico).label("ingredient"),
        func.avg(CenabastProduct.precio_maximo_publico).label("avg_pmvp"),
        func.count(CenabastProduct.id).label("product_count"),
    ).filter(
        CenabastProduct.nombre_generico.isnot(None),
        CenabastProduct.precio_maximo_publico.isnot(None),
        CenabastProduct.precio_maximo_publico > 0,
    ).group_by(
        func.lower(CenabastProduct.nombre_generico)
    ).all()

    return {row.ingredient: {"avg_pmvp": float(row.avg_pmvp), "count": int(row.product_count)} for row in rows}


def _match_ingredient(ingredient: str, cost_map: dict):
    """Find best match: exact first, then substring."""
    ingredient = ingredient.strip().lower()
    if ingredient in cost_map:
        return cost_map[ingredient]
    for key, val in cost_map.items():
        if ingredient in key or key in ingredient:
            return val
    return None


def get_cenabast_cost_for_medication(db: Session, medication_id: str):
    med = db.query(Medication).filter(Medication.id == medication_id).first()
    if not med or not med.active_ingredient:
        return None

    cost_map = _build_cost_map(db)
    match = _match_ingredient(med.active_ingredient, cost_map)
    if not match:
        return None

    return {
        "avg_cenabast_cost": round(match["avg_pmvp"], 0),
        "precio_maximo_publico": round(match["avg_pmvp"], 0),
        "invoice_count": match["count"],
    }


def get_pharmacy_markup(db: Session, medication_id: str):
    cenabast = get_cenabast_cost_for_medication(db, medication_id)
    if not cenabast:
        return []

    cost = cenabast["avg_cenabast_cost"]

    rows = db.query(Price, Pharmacy).join(
        Pharmacy, Price.pharmacy_id == Pharmacy.id
    ).filter(
        Price.medication_id == medication_id,
        Price.in_stock == True,
        Price.price > 0,
    ).order_by(Price.price).all()

    results = []
    for price, pharmacy in rows:
        markup_pct = round((price.price - cost) / cost * 100, 1) if cost > 0 else 0
        results.append({
            "pharmacy_name": pharmacy.name,
            "chain": pharmacy.chain,
            "retail_price": price.price,
            "cenabast_cost": cost,
            "markup_pct": markup_pct,
            "is_precio_justo": markup_pct <= 100,
        })
    return results


def get_most_overpriced_medications(db: Session, limit: int = 50):
    cost_map = _build_cost_map(db)

    # Get avg retail price per medication
    rows = db.query(
        Medication.id,
        Medication.name,
        Medication.active_ingredient,
        func.avg(Price.price).label("avg_retail"),
    ).join(
        Price, Price.medication_id == Medication.id
    ).filter(
        Medication.active_ingredient.isnot(None),
        Price.price > 0,
        Price.in_stock == True,
    ).group_by(
        Medication.id, Medication.name, Medication.active_ingredient
    ).all()

    results = []
    for row in rows:
        match = _match_ingredient(row.active_ingredient, cost_map)
        if not match:
            continue
        avg_retail = float(row.avg_retail)
        avg_cost = match["avg_pmvp"]
        if avg_cost <= 0:
            continue
        markup_pct = round((avg_retail - avg_cost) / avg_cost * 100, 1)
        if markup_pct <= 0:
            continue
        results.append({
            "medication_id": str(row.id),
            "medication_name": row.name,
            "active_ingredient": row.active_ingredient,
            "avg_retail": round(avg_retail, 0),
            "cenabast_cost": round(avg_cost, 0),
            "markup_pct": markup_pct,
        })

    results.sort(key=lambda x: x["markup_pct"], reverse=True)
    return results[:limit]


def get_pharmacy_transparency_index(db: Session):
    cost_map = _build_cost_map(db)

    # Get avg retail price per chain+medication
    rows = db.query(
        Pharmacy.chain,
        Medication.active_ingredient,
        func.avg(Price.price).label("avg_retail"),
        func.count(func.distinct(Medication.id)).label("med_count"),
    ).join(
        Price, Price.pharmacy_id == Pharmacy.id
    ).join(
        Medication, Price.medication_id == Medication.id
    ).filter(
        Medication.active_ingredient.isnot(None),
        Price.price > 0,
        Price.in_stock == True,
    ).group_by(
        Pharmacy.chain, Medication.active_ingredient
    ).all()

    chain_data = {}
    for row in rows:
        match = _match_ingredient(row.active_ingredient, cost_map)
        if not match:
            continue
        avg_retail = float(row.avg_retail)
        avg_cost = match["avg_pmvp"]
        if avg_cost <= 0:
            continue
        markup = (avg_retail - avg_cost) / avg_cost * 100

        chain = row.chain or "Otra"
        if chain not in chain_data:
            chain_data[chain] = {"markups": [], "med_count": 0}
        chain_data[chain]["markups"].append(markup)
        chain_data[chain]["med_count"] += int(row.med_count)

    results = []
    for chain, data in chain_data.items():
        avg_markup = round(sum(data["markups"]) / len(data["markups"]), 1)
        transparency_score = max(0, min(100, round(100 - (avg_markup / 5), 0)))
        results.append({
            "chain": chain,
            "avg_markup_pct": avg_markup,
            "medication_count": data["med_count"],
            "transparency_score": transparency_score,
        })
    results.sort(key=lambda x: x["transparency_score"], reverse=True)
    return results


def get_transparency_stats(db: Session):
    total_meds = db.query(func.count(Medication.id)).scalar() or 0

    cost_map = _build_cost_map(db)

    # Count medications that have a match in CenabastProduct
    all_meds = db.query(Medication.active_ingredient).filter(
        Medication.active_ingredient.isnot(None),
    ).distinct().all()

    matched_count = sum(1 for (ing,) in all_meds if _match_ingredient(ing, cost_map))

    avg_cenabast = sum(v["avg_pmvp"] for v in cost_map.values()) / len(cost_map) if cost_map else 0

    avg_retail = db.query(func.avg(Price.price)).filter(
        Price.price > 0, Price.in_stock == True
    ).scalar()

    avg_markup = 0
    if avg_cenabast and avg_retail and avg_cenabast > 0:
        avg_markup = round((float(avg_retail) - avg_cenabast) / avg_cenabast * 100, 1)

    return {
        "total_medications": total_meds,
        "medications_with_transparency": matched_count,
        "avg_cenabast_cost": round(avg_cenabast, 0),
        "avg_retail_price": round(float(avg_retail), 0) if avg_retail else 0,
        "avg_markup_pct": avg_markup,
    }
