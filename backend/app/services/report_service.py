import csv
import io
from sqlalchemy.orm import Session

from app.models.saved_report import SavedReport
from app.services import analytics as analytics_svc
from app.services.forecasting_service import get_upcoming_opportunities
from app.services.competitive_intel_service import (
    get_market_share_trends,
    get_supplier_win_rates,
    detect_new_entrants,
    get_price_positioning,
)


def execute_report(db: Session, query_config: dict):
    dataset = query_config.get("dataset", "")
    filters = query_config.get("filters", {})
    limit = query_config.get("limit", 100)

    dataset_map = {
        "market-share": lambda: analytics_svc.get_market_share(db, market=filters.get("market")),
        "sales-trends": lambda: analytics_svc.get_sales_trends(db, drug=filters.get("drug")),
        "top-institutions": lambda: analytics_svc.get_top_institutions(
            db, limit=limit, region=filters.get("region")
        ),
        "regional": lambda: analytics_svc.get_regional_distribution(db),
        "cenabast-trends": lambda: analytics_svc.get_cenabast_trends(db, product=filters.get("product")),
        "cenabast-top-products": lambda: analytics_svc.get_cenabast_top_products(db, limit=limit),
        "cenabast-regional": lambda: analytics_svc.get_cenabast_regional(db),
        "forecasts": lambda: get_upcoming_opportunities(
            db,
            days_ahead=int(filters.get("days_ahead", 90)),
            product=filters.get("product"),
            region=filters.get("region"),
        ),
        "market-share-trends": lambda: get_market_share_trends(
            db, product=filters.get("product"), months=int(filters.get("months", 24))
        ),
        "supplier-win-rates": lambda: get_supplier_win_rates(
            db, supplier=filters.get("supplier")
        ),
        "new-entrants": lambda: detect_new_entrants(
            db, lookback_months=int(filters.get("lookback_months", 6))
        ),
        "price-positioning": lambda: get_price_positioning(
            db, product=filters.get("product"), supplier=filters.get("supplier")
        ),
        "regional-heatmap": lambda: analytics_svc.get_regional_demand_heatmap(
            db, product=filters.get("product")
        ),
    }

    handler = dataset_map.get(dataset)
    if not handler:
        return {"error": f"Unknown dataset: {dataset}"}

    data = handler()

    columns = query_config.get("columns", [])
    if columns and data:
        data = [{k: v for k, v in row.items() if k in columns} for row in data]

    sort_by = query_config.get("sort_by")
    if sort_by and data:
        reverse = sort_by.startswith("-")
        key = sort_by.lstrip("-")
        if key in data[0]:
            data.sort(key=lambda x: x.get(key, 0) or 0, reverse=reverse)

    return data[:limit]


def save_report(db: Session, org_id: str, name: str, query_config: dict, schedule: str = "none", schedule_recipients: str = None):
    report = SavedReport(
        org_id=org_id,
        name=name,
        query_config=query_config,
        schedule=schedule,
        schedule_recipients=schedule_recipients,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def list_reports(db: Session, org_id: str):
    return db.query(SavedReport).filter(SavedReport.org_id == org_id).order_by(SavedReport.created_at.desc()).all()


def delete_report(db: Session, report_id: str, org_id: str):
    report = db.query(SavedReport).filter(
        SavedReport.id == report_id,
        SavedReport.org_id == org_id,
    ).first()
    if report:
        db.delete(report)
        db.commit()
        return True
    return False


def generate_csv(data: list[dict]) -> str:
    if not data:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()
