from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cenabast_invoice import CenabastInvoice
from app.models.cenabast_product import CenabastProduct
from app.models.medication import Medication
from app.models.pharmacy import Pharmacy
from app.models.price import Price


def get_cenabast_cost_for_medication(db: Session, medication_id: str):
    med = db.query(Medication).filter(Medication.id == medication_id).first()
    if not med or not med.active_ingredient:
        return None

    ingredient = med.active_ingredient.strip().lower()

    row = db.query(
        func.avg(CenabastInvoice.costo_producto).label("avg_cenabast_cost"),
        func.count(CenabastInvoice.id).label("invoice_count"),
    ).filter(
        func.lower(CenabastInvoice.nombre_material_generico).contains(ingredient),
        CenabastInvoice.costo_producto.isnot(None),
        CenabastInvoice.costo_producto > 0,
    ).first()

    if not row or not row.avg_cenabast_cost:
        return None

    pmvp = db.query(func.avg(CenabastProduct.precio_maximo_publico)).filter(
        func.lower(CenabastProduct.nombre_generico).contains(ingredient),
        CenabastProduct.precio_maximo_publico.isnot(None),
        CenabastProduct.precio_maximo_publico > 0,
    ).scalar()

    return {
        "avg_cenabast_cost": round(float(row.avg_cenabast_cost), 0),
        "precio_maximo_publico": round(float(pmvp), 0) if pmvp else None,
        "invoice_count": int(row.invoice_count),
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
    med_ingredient = func.lower(Medication.active_ingredient)
    inv_ingredient = func.lower(CenabastInvoice.nombre_material_generico)

    rows = db.query(
        Medication.id.label("medication_id"),
        Medication.name.label("medication_name"),
        Medication.active_ingredient,
        func.avg(Price.price).label("avg_retail"),
        func.avg(CenabastInvoice.costo_producto).label("avg_cenabast_cost"),
    ).join(
        Price, Price.medication_id == Medication.id
    ).join(
        CenabastInvoice,
        inv_ingredient.contains(med_ingredient),
    ).filter(
        Medication.active_ingredient.isnot(None),
        Price.price > 0,
        Price.in_stock == True,
        CenabastInvoice.costo_producto.isnot(None),
        CenabastInvoice.costo_producto > 0,
    ).group_by(
        Medication.id, Medication.name, Medication.active_ingredient
    ).having(
        func.avg(Price.price) > 0,
        func.avg(CenabastInvoice.costo_producto) > 0,
    ).order_by(
        (func.avg(Price.price) / func.avg(CenabastInvoice.costo_producto)).desc()
    ).limit(limit).all()

    results = []
    for row in rows:
        avg_retail = float(row.avg_retail)
        avg_cost = float(row.avg_cenabast_cost)
        markup_pct = round((avg_retail - avg_cost) / avg_cost * 100, 1) if avg_cost > 0 else 0
        results.append({
            "medication_id": str(row.medication_id),
            "medication_name": row.medication_name,
            "active_ingredient": row.active_ingredient,
            "avg_retail": round(avg_retail, 0),
            "cenabast_cost": round(avg_cost, 0),
            "markup_pct": markup_pct,
        })
    return results


def get_pharmacy_transparency_index(db: Session):
    med_ingredient = func.lower(Medication.active_ingredient)
    inv_ingredient = func.lower(CenabastInvoice.nombre_material_generico)

    rows = db.query(
        Pharmacy.chain,
        func.avg(Price.price).label("avg_retail"),
        func.avg(CenabastInvoice.costo_producto).label("avg_cenabast_cost"),
        func.count(func.distinct(Medication.id)).label("medication_count"),
    ).join(
        Price, Price.pharmacy_id == Pharmacy.id
    ).join(
        Medication, Price.medication_id == Medication.id
    ).join(
        CenabastInvoice,
        inv_ingredient.contains(med_ingredient),
    ).filter(
        Medication.active_ingredient.isnot(None),
        Price.price > 0,
        Price.in_stock == True,
        CenabastInvoice.costo_producto.isnot(None),
        CenabastInvoice.costo_producto > 0,
    ).group_by(Pharmacy.chain).all()

    results = []
    for row in rows:
        avg_retail = float(row.avg_retail)
        avg_cost = float(row.avg_cenabast_cost)
        avg_markup = round((avg_retail - avg_cost) / avg_cost * 100, 1) if avg_cost > 0 else 0
        # Score: 100 = no markup, 0 = 500%+ markup
        transparency_score = max(0, min(100, round(100 - (avg_markup / 5), 0)))
        results.append({
            "chain": row.chain,
            "avg_markup_pct": avg_markup,
            "medication_count": int(row.medication_count),
            "transparency_score": transparency_score,
        })
    results.sort(key=lambda x: x["transparency_score"], reverse=True)
    return results


def get_transparency_stats(db: Session):
    total_meds = db.query(func.count(Medication.id)).scalar() or 0

    meds_with_data = db.query(func.count(func.distinct(Medication.id))).join(
        Price, Price.medication_id == Medication.id
    ).filter(
        Medication.active_ingredient.isnot(None),
    ).scalar() or 0

    avg_cenabast = db.query(func.avg(CenabastInvoice.costo_producto)).filter(
        CenabastInvoice.costo_producto.isnot(None),
        CenabastInvoice.costo_producto > 0,
    ).scalar()

    avg_retail = db.query(func.avg(Price.price)).filter(
        Price.price > 0, Price.in_stock == True
    ).scalar()

    avg_markup = 0
    if avg_cenabast and avg_retail and avg_cenabast > 0:
        avg_markup = round((float(avg_retail) - float(avg_cenabast)) / float(avg_cenabast) * 100, 1)

    return {
        "total_medications": total_meds,
        "medications_with_transparency": meds_with_data,
        "avg_cenabast_cost": round(float(avg_cenabast), 0) if avg_cenabast else 0,
        "avg_retail_price": round(float(avg_retail), 0) if avg_retail else 0,
        "avg_markup_pct": avg_markup,
    }
