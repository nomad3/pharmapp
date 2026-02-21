from sqlalchemy import func, distinct, case, cast, String
from sqlalchemy.orm import Session

from app.models.bms_distribution import BmsDistribution
from app.models.bms_purchase_order import BmsPurchaseOrder
from app.models.bms_adjudication import BmsAdjudication
from app.models.bms_institution import BmsInstitution
from app.models.cenabast_product import CenabastProduct
from app.models.cenabast_invoice import CenabastInvoice
from app.models.medication import Medication


# ── BMS Analytics ──────────────────────────────────────────────


def get_dashboard_summary(db: Session):
    bms_dist = db.query(func.count(BmsDistribution.id)).scalar() or 0
    bms_po = db.query(func.count(BmsPurchaseOrder.id)).scalar() or 0
    bms_adj = db.query(func.count(BmsAdjudication.id)).scalar() or 0
    bms_inst = db.query(func.count(BmsInstitution.id)).scalar() or 0
    bms_rev = db.query(func.coalesce(func.sum(BmsDistribution.net_amount), 0)).scalar()

    cn_prod = db.query(func.count(CenabastProduct.id)).scalar() or 0
    cn_inv = db.query(func.count(CenabastInvoice.id)).scalar() or 0
    cn_rev = db.query(func.coalesce(func.sum(CenabastInvoice.monto_bruto), 0)).scalar()

    total_drugs = db.query(func.count(Medication.id)).scalar() or 0

    return {
        "bms_distribution_records": bms_dist,
        "bms_purchase_orders": bms_po,
        "bms_adjudications": bms_adj,
        "bms_institutions": bms_inst,
        "bms_total_revenue": float(bms_rev),
        "cenabast_products": cn_prod,
        "cenabast_invoices": cn_inv,
        "cenabast_total_revenue": float(cn_rev),
        "total_drugs": total_drugs,
    }


def get_market_share(db: Session, market: str = None):
    q = db.query(
        BmsDistribution.active_ingredient.label("drug"),
        BmsDistribution.market,
        func.sum(
            case(
                (BmsDistribution.bms_competition.ilike("%bms%"), BmsDistribution.unit_quantity),
                else_=0,
            )
        ).label("bms_units"),
        func.sum(
            case(
                (BmsDistribution.bms_competition.not_ilike("%bms%"), BmsDistribution.unit_quantity),
                else_=0,
            )
        ).label("competition_units"),
    ).group_by(BmsDistribution.active_ingredient, BmsDistribution.market)

    if market:
        q = q.filter(BmsDistribution.market.ilike(f"%{market}%"))

    q = q.having(func.sum(BmsDistribution.unit_quantity) > 0)
    q = q.order_by(func.sum(BmsDistribution.unit_quantity).desc())

    results = []
    for row in q.limit(50).all():
        total = (row.bms_units or 0) + (row.competition_units or 0)
        results.append({
            "drug": row.drug or "Unknown",
            "market": row.market,
            "bms_units": int(row.bms_units or 0),
            "competition_units": int(row.competition_units or 0),
            "bms_share_pct": round((row.bms_units or 0) / total * 100, 1) if total > 0 else 0,
        })
    return results


def get_sales_trends(db: Session, drug: str = None):
    date_trunc = func.date_trunc("month", BmsDistribution.delivery_date)
    q = db.query(
        cast(date_trunc, String).label("period"),
        func.sum(
            case(
                (BmsDistribution.bms_competition.ilike("%bms%"), BmsDistribution.net_amount),
                else_=0,
            )
        ).label("bms_revenue"),
        func.sum(
            case(
                (BmsDistribution.bms_competition.not_ilike("%bms%"), BmsDistribution.net_amount),
                else_=0,
            )
        ).label("competition_revenue"),
        func.sum(BmsDistribution.unit_quantity).label("total_units"),
    ).filter(BmsDistribution.delivery_date.isnot(None)).group_by(date_trunc).order_by(date_trunc)

    if drug:
        q = q.filter(BmsDistribution.active_ingredient.ilike(f"%{drug}%"))

    results = []
    for row in q.all():
        results.append({
            "period": row.period[:7] if row.period else "",
            "bms_revenue": float(row.bms_revenue or 0),
            "competition_revenue": float(row.competition_revenue or 0),
            "total_units": int(row.total_units or 0),
        })
    return results


def get_top_institutions(db: Session, limit: int = 20, region: str = None):
    q = db.query(
        BmsDistribution.institution_rut.label("rut"),
        func.max(BmsDistribution.client_destination_name).label("razon_social"),
        func.max(BmsDistribution.region).label("region"),
        func.sum(BmsDistribution.unit_quantity).label("total_units"),
        func.sum(BmsDistribution.net_amount).label("total_revenue"),
    ).filter(
        BmsDistribution.institution_rut.isnot(None)
    ).group_by(BmsDistribution.institution_rut)

    if region:
        q = q.filter(BmsDistribution.region.ilike(f"%{region}%"))

    q = q.order_by(func.sum(BmsDistribution.net_amount).desc())

    results = []
    for row in q.limit(limit).all():
        results.append({
            "rut": row.rut,
            "razon_social": row.razon_social,
            "region": row.region,
            "total_units": int(row.total_units or 0),
            "total_revenue": float(row.total_revenue or 0),
        })
    return results


def get_regional_distribution(db: Session):
    q = db.query(
        BmsDistribution.region.label("region"),
        func.sum(BmsDistribution.unit_quantity).label("total_units"),
        func.sum(BmsDistribution.net_amount).label("total_revenue"),
        func.count(distinct(BmsDistribution.institution_rut)).label("institution_count"),
    ).filter(
        BmsDistribution.region.isnot(None)
    ).group_by(BmsDistribution.region).order_by(func.sum(BmsDistribution.net_amount).desc())

    results = []
    for row in q.all():
        results.append({
            "region": row.region,
            "total_units": int(row.total_units or 0),
            "total_revenue": float(row.total_revenue or 0),
            "institution_count": int(row.institution_count or 0),
        })
    return results


def get_drug_prices(db: Session, drug: str = None):
    q = db.query(
        BmsDistribution.active_ingredient.label("drug"),
        func.avg(
            case(
                (BmsDistribution.bms_competition.ilike("%bms%"), BmsDistribution.net_unit_price),
                else_=None,
            )
        ).label("avg_price_bms"),
        func.avg(
            case(
                (BmsDistribution.bms_competition.not_ilike("%bms%"), BmsDistribution.net_unit_price),
                else_=None,
            )
        ).label("avg_price_competition"),
        func.min(BmsDistribution.net_unit_price).label("min_price"),
        func.max(BmsDistribution.net_unit_price).label("max_price"),
    ).filter(
        BmsDistribution.net_unit_price.isnot(None),
        BmsDistribution.net_unit_price > 0,
    ).group_by(BmsDistribution.active_ingredient)

    if drug:
        q = q.filter(BmsDistribution.active_ingredient.ilike(f"%{drug}%"))

    q = q.order_by(BmsDistribution.active_ingredient)

    results = []
    for row in q.all():
        results.append({
            "drug": row.drug or "Unknown",
            "avg_price_bms": round(float(row.avg_price_bms), 0) if row.avg_price_bms else None,
            "avg_price_competition": round(float(row.avg_price_competition), 0) if row.avg_price_competition else None,
            "min_price": round(float(row.min_price), 0) if row.min_price else None,
            "max_price": round(float(row.max_price), 0) if row.max_price else None,
        })
    return results


# ── Cenabast Analytics ─────────────────────────────────────────


def get_cenabast_trends(db: Session, product: str = None):
    q = db.query(
        CenabastInvoice.ano.label("ano"),
        CenabastInvoice.mes.label("mes"),
        func.sum(CenabastInvoice.monto_bruto).label("total_revenue"),
        func.sum(CenabastInvoice.cantidad_unitaria).label("total_units"),
        func.count(CenabastInvoice.id).label("invoice_count"),
    ).filter(
        CenabastInvoice.ano.isnot(None)
    ).group_by(CenabastInvoice.ano, CenabastInvoice.mes).order_by(
        CenabastInvoice.ano, CenabastInvoice.mes
    )

    if product:
        q = q.filter(CenabastInvoice.nombre_producto_comercial.ilike(f"%{product}%"))

    results = []
    for row in q.all():
        period = f"{row.ano}-{str(row.mes).zfill(2)}" if row.mes else str(row.ano)
        results.append({
            "period": period,
            "total_revenue": float(row.total_revenue or 0),
            "total_units": int(row.total_units or 0),
            "invoice_count": int(row.invoice_count or 0),
        })
    return results


def get_cenabast_top_pharmacies(db: Session, limit: int = 20, region: str = None):
    q = db.query(
        CenabastInvoice.rut_cliente_solicitante.label("rut"),
        func.max(CenabastInvoice.nombre_cliente_solicitante).label("nombre"),
        func.max(CenabastInvoice.comuna_solicitante).label("comuna"),
        func.max(CenabastInvoice.region_solicitante).label("region"),
        func.sum(CenabastInvoice.cantidad_unitaria).label("total_units"),
        func.sum(CenabastInvoice.monto_bruto).label("total_revenue"),
    ).filter(
        CenabastInvoice.rut_cliente_solicitante.isnot(None)
    ).group_by(CenabastInvoice.rut_cliente_solicitante)

    if region:
        q = q.filter(CenabastInvoice.region_solicitante.ilike(f"%{region}%"))

    q = q.order_by(func.sum(CenabastInvoice.monto_bruto).desc())

    results = []
    for row in q.limit(limit).all():
        results.append({
            "rut": row.rut,
            "nombre": row.nombre,
            "comuna": row.comuna,
            "region": row.region,
            "total_units": int(row.total_units or 0),
            "total_revenue": float(row.total_revenue or 0),
        })
    return results


def get_cenabast_top_products(db: Session, limit: int = 20):
    q = db.query(
        CenabastInvoice.codigo_producto_comercial.label("codigo"),
        func.max(CenabastInvoice.nombre_producto_comercial).label("nombre"),
        func.sum(CenabastInvoice.cantidad_unitaria).label("total_units"),
        func.sum(CenabastInvoice.monto_bruto).label("total_revenue"),
    ).filter(
        CenabastInvoice.codigo_producto_comercial.isnot(None)
    ).group_by(CenabastInvoice.codigo_producto_comercial).order_by(
        func.sum(CenabastInvoice.monto_bruto).desc()
    )

    results = []
    for row in q.limit(limit).all():
        # Look up max price from products catalog
        prod = db.query(CenabastProduct.precio_maximo_publico).filter(
            CenabastProduct.codigo_producto == row.codigo
        ).first()
        results.append({
            "codigo": row.codigo,
            "nombre": row.nombre,
            "total_units": int(row.total_units or 0),
            "total_revenue": float(row.total_revenue or 0),
            "precio_maximo": float(prod[0]) if prod and prod[0] else None,
        })
    return results


def get_cenabast_regional(db: Session):
    q = db.query(
        CenabastInvoice.region_solicitante.label("region"),
        func.sum(CenabastInvoice.cantidad_unitaria).label("total_units"),
        func.sum(CenabastInvoice.monto_bruto).label("total_revenue"),
        func.count(distinct(CenabastInvoice.rut_cliente_solicitante)).label("pharmacy_count"),
    ).filter(
        CenabastInvoice.region_solicitante.isnot(None)
    ).group_by(CenabastInvoice.region_solicitante).order_by(
        func.sum(CenabastInvoice.monto_bruto).desc()
    )

    results = []
    for row in q.all():
        results.append({
            "region": row.region,
            "total_units": int(row.total_units or 0),
            "total_revenue": float(row.total_revenue or 0),
            "pharmacy_count": int(row.pharmacy_count or 0),
        })
    return results
