from sqlalchemy import func, cast, String, distinct
from sqlalchemy.orm import Session

from app.models.bms_distribution import BmsDistribution
from app.models.bms_adjudication import BmsAdjudication


def get_market_share_trends(db: Session, product: str = None, months: int = 24):
    date_trunc = func.date_trunc("month", BmsDistribution.delivery_date)

    q = db.query(
        cast(date_trunc, String).label("period"),
        BmsDistribution.bms_competition.label("provider"),
        func.sum(BmsDistribution.unit_quantity).label("units"),
        func.sum(BmsDistribution.net_amount).label("revenue"),
    ).filter(
        BmsDistribution.delivery_date.isnot(None),
        BmsDistribution.bms_competition.isnot(None),
    ).group_by(date_trunc, BmsDistribution.bms_competition).order_by(date_trunc)

    if product:
        q = q.filter(BmsDistribution.active_ingredient.ilike(f"%{product}%"))

    results = []
    for row in q.all():
        results.append({
            "period": row.period[:7] if row.period else "",
            "provider": row.provider,
            "units": int(row.units or 0),
            "revenue": float(row.revenue or 0),
        })
    return results


def get_supplier_win_rates(db: Session, supplier: str = None):
    q = db.query(
        BmsAdjudication.corp_proveedor.label("supplier"),
        func.count(BmsAdjudication.id).label("total_bids"),
        func.sum(
            func.cast(
                BmsAdjudication.estado.ilike("%adjudicad%"),
                db.bind.dialect.type_descriptor(type(1)) if db.bind else type(1),
            )
        ),
    ).filter(
        BmsAdjudication.corp_proveedor.isnot(None),
    ).group_by(BmsAdjudication.corp_proveedor)

    if supplier:
        q = q.filter(BmsAdjudication.corp_proveedor.ilike(f"%{supplier}%"))

    # Simpler approach: query total and wins separately
    total_q = db.query(
        BmsAdjudication.corp_proveedor.label("supplier"),
        func.count(BmsAdjudication.id).label("total_bids"),
    ).filter(
        BmsAdjudication.corp_proveedor.isnot(None),
    ).group_by(BmsAdjudication.corp_proveedor)

    wins_q = db.query(
        BmsAdjudication.corp_proveedor.label("supplier"),
        func.count(BmsAdjudication.id).label("wins"),
    ).filter(
        BmsAdjudication.corp_proveedor.isnot(None),
        BmsAdjudication.estado.ilike("%adjudicad%"),
    ).group_by(BmsAdjudication.corp_proveedor)

    if supplier:
        total_q = total_q.filter(BmsAdjudication.corp_proveedor.ilike(f"%{supplier}%"))
        wins_q = wins_q.filter(BmsAdjudication.corp_proveedor.ilike(f"%{supplier}%"))

    totals = {r.supplier: r.total_bids for r in total_q.all()}
    wins = {r.supplier: r.wins for r in wins_q.all()}

    results = []
    for s, total in totals.items():
        w = wins.get(s, 0)
        results.append({
            "supplier": s,
            "total_bids": total,
            "wins": w,
            "win_rate_pct": round(w / total * 100, 1) if total > 0 else 0,
        })
    results.sort(key=lambda x: x["win_rate_pct"], reverse=True)
    return results


def detect_new_entrants(db: Session, lookback_months: int = 6):
    from datetime import date, timedelta
    cutoff = date.today() - timedelta(days=lookback_months * 30)

    recent = db.query(
        distinct(BmsDistribution.provider_name)
    ).filter(
        BmsDistribution.delivery_date >= cutoff,
        BmsDistribution.provider_name.isnot(None),
    ).all()
    recent_names = {r[0] for r in recent}

    older = db.query(
        distinct(BmsDistribution.provider_name)
    ).filter(
        BmsDistribution.delivery_date < cutoff,
        BmsDistribution.provider_name.isnot(None),
    ).all()
    older_names = {r[0] for r in older}

    new_entrants = recent_names - older_names
    results = []
    for name in new_entrants:
        first_record = db.query(
            func.min(BmsDistribution.delivery_date).label("first_seen"),
            func.sum(BmsDistribution.unit_quantity).label("total_units"),
            func.sum(BmsDistribution.net_amount).label("total_revenue"),
        ).filter(
            BmsDistribution.provider_name == name
        ).first()

        results.append({
            "supplier": name,
            "first_seen": str(first_record.first_seen) if first_record.first_seen else None,
            "total_units": int(first_record.total_units or 0),
            "total_revenue": float(first_record.total_revenue or 0),
        })

    results.sort(key=lambda x: x["total_revenue"], reverse=True)
    return results


def get_price_positioning(db: Session, product: str = None, supplier: str = None):
    q = db.query(
        BmsDistribution.provider_name.label("supplier"),
        func.avg(BmsDistribution.net_unit_price).label("avg_price"),
        func.min(BmsDistribution.net_unit_price).label("min_price"),
        func.max(BmsDistribution.net_unit_price).label("max_price"),
        func.count(BmsDistribution.id).label("transaction_count"),
    ).filter(
        BmsDistribution.net_unit_price.isnot(None),
        BmsDistribution.net_unit_price > 0,
        BmsDistribution.provider_name.isnot(None),
    ).group_by(BmsDistribution.provider_name)

    if product:
        q = q.filter(BmsDistribution.active_ingredient.ilike(f"%{product}%"))
    if supplier:
        q = q.filter(BmsDistribution.provider_name.ilike(f"%{supplier}%"))

    # Get overall market average
    market_avg_q = db.query(
        func.avg(BmsDistribution.net_unit_price)
    ).filter(
        BmsDistribution.net_unit_price.isnot(None),
        BmsDistribution.net_unit_price > 0,
    )
    if product:
        market_avg_q = market_avg_q.filter(BmsDistribution.active_ingredient.ilike(f"%{product}%"))

    market_avg = float(market_avg_q.scalar() or 0)

    results = []
    for row in q.order_by(func.avg(BmsDistribution.net_unit_price)).all():
        avg_p = float(row.avg_price)
        vs_market = round((avg_p - market_avg) / market_avg * 100, 1) if market_avg > 0 else 0
        results.append({
            "supplier": row.supplier,
            "avg_price": round(avg_p, 0),
            "min_price": round(float(row.min_price), 0),
            "max_price": round(float(row.max_price), 0),
            "vs_market_pct": vs_market,
            "transaction_count": int(row.transaction_count),
            "market_avg": round(market_avg, 0),
        })
    return results
