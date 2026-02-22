from datetime import timedelta
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from app.models.cenabast_invoice import CenabastInvoice


def forecast_institution_restock(db: Session, institution_rut: str, product: str = None):
    q = db.query(
        CenabastInvoice.nombre_material_generico,
        CenabastInvoice.fecha_doc,
        func.sum(CenabastInvoice.cantidad_unitaria).label("quantity"),
    ).filter(
        CenabastInvoice.rut_cliente_solicitante == institution_rut,
        CenabastInvoice.fecha_doc.isnot(None),
    )

    if product:
        q = q.filter(CenabastInvoice.nombre_material_generico.ilike(f"%{product}%"))

    q = q.group_by(
        CenabastInvoice.nombre_material_generico,
        CenabastInvoice.fecha_doc,
    ).order_by(
        CenabastInvoice.nombre_material_generico,
        CenabastInvoice.fecha_doc,
    )

    rows = q.all()

    # Group by product
    products = {}
    for row in rows:
        name = row.nombre_material_generico or "Unknown"
        if name not in products:
            products[name] = []
        products[name].append({
            "date": row.fecha_doc,
            "quantity": int(row.quantity or 0),
        })

    forecasts = []
    for prod_name, purchases in products.items():
        if len(purchases) < 2:
            continue

        dates = sorted([p["date"] for p in purchases])
        intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
        intervals = [i for i in intervals if i > 0]

        if not intervals:
            continue

        mean_interval = sum(intervals) / len(intervals)
        last_date = dates[-1]
        predicted_next = last_date + timedelta(days=int(mean_interval))

        avg_quantity = sum(p["quantity"] for p in purchases) / len(purchases)

        n = len(purchases)
        confidence = "low" if n < 5 else "medium" if n < 10 else "high"

        std_dev = (sum((i - mean_interval) ** 2 for i in intervals) / len(intervals)) ** 0.5 if len(intervals) > 1 else mean_interval * 0.5
        confidence_low = last_date + timedelta(days=max(1, int(mean_interval - std_dev)))
        confidence_high = last_date + timedelta(days=int(mean_interval + std_dev))

        forecasts.append({
            "product": prod_name,
            "institution_rut": institution_rut,
            "last_purchase_date": str(last_date),
            "predicted_next_date": str(predicted_next),
            "confidence_low": str(confidence_low),
            "confidence_high": str(confidence_high),
            "avg_quantity": round(avg_quantity),
            "confidence_level": confidence,
            "purchase_count": n,
        })

    forecasts.sort(key=lambda x: x["predicted_next_date"])
    return forecasts


def get_upcoming_opportunities(
    db: Session,
    days_ahead: int = 90,
    product: str = None,
    region: str = None,
):
    from datetime import date

    rut_q = db.query(
        distinct(CenabastInvoice.rut_cliente_solicitante)
    ).filter(CenabastInvoice.rut_cliente_solicitante.isnot(None))

    if region:
        rut_q = rut_q.filter(CenabastInvoice.region_solicitante.ilike(f"%{region}%"))

    ruts = [r[0] for r in rut_q.limit(200).all()]

    today = date.today()
    cutoff = today + timedelta(days=days_ahead)

    opportunities = []
    for rut in ruts:
        forecasts = forecast_institution_restock(db, rut, product=product)
        for f in forecasts:
            pred_date = f["predicted_next_date"]
            if pred_date <= str(cutoff):
                from datetime import datetime
                pred_dt = datetime.strptime(pred_date, "%Y-%m-%d").date()
                days_until = (pred_dt - today).days

                institution_name = db.query(
                    CenabastInvoice.nombre_cliente_solicitante
                ).filter(
                    CenabastInvoice.rut_cliente_solicitante == rut
                ).first()

                avg_cost = db.query(
                    func.avg(CenabastInvoice.costo_producto)
                ).filter(
                    CenabastInvoice.rut_cliente_solicitante == rut,
                    CenabastInvoice.nombre_material_generico.ilike(f"%{f['product']}%"),
                    CenabastInvoice.costo_producto > 0,
                ).scalar()

                est_value = float(avg_cost or 0) * f["avg_quantity"]

                opportunities.append({
                    "product": f["product"],
                    "institution_rut": rut,
                    "institution_name": institution_name[0] if institution_name else None,
                    "predicted_date": pred_date,
                    "days_until": days_until,
                    "estimated_value": round(est_value, 0),
                    "confidence_level": f["confidence_level"],
                    "avg_quantity": f["avg_quantity"],
                })

    opportunities.sort(key=lambda x: x["days_until"])
    return opportunities[:100]
