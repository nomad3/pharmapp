import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_api_key
from app.services import analytics as svc

router = APIRouter(prefix="/data", tags=["data-api"])


@router.get("/prices")
def get_prices(
    medication: Optional[str] = Query(None),
    pharmacy: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    from app.models.price import Price
    from app.models.medication import Medication
    from app.models.pharmacy import Pharmacy

    q = db.query(Price, Medication, Pharmacy).join(
        Medication, Price.medication_id == Medication.id
    ).join(Pharmacy, Price.pharmacy_id == Pharmacy.id)

    if medication:
        q = q.filter(
            Medication.name.ilike(f"%{medication}%")
            | Medication.active_ingredient.ilike(f"%{medication}%")
        )
    if pharmacy:
        q = q.filter(Pharmacy.chain.ilike(f"%{pharmacy}%") | Pharmacy.name.ilike(f"%{pharmacy}%"))

    rows = q.limit(limit).all()
    return [
        {
            "medication_name": med.name,
            "active_ingredient": med.active_ingredient,
            "dosage": med.dosage,
            "pharmacy_chain": pharm.chain,
            "pharmacy_name": pharm.name,
            "pharmacy_comuna": pharm.comuna,
            "price": p.price,
            "in_stock": p.in_stock,
            "scraped_at": str(p.scraped_at) if p.scraped_at else None,
        }
        for p, med, pharm in rows
    ]


@router.get("/market-share")
def get_market_share(
    market: Optional[str] = Query(None),
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    return svc.get_market_share(db, market=market)


@router.get("/procurement")
def get_procurement(
    region: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    return svc.get_top_institutions(db, limit=limit, region=region)


@router.get("/trends")
def get_trends(
    drug: Optional[str] = Query(None),
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    return svc.get_sales_trends(db, drug=drug)


@router.get("/institutions")
def get_institutions(
    region: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    return svc.get_top_institutions(db, limit=limit, region=region)


@router.get("/regions")
def get_regions(
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    return svc.get_regional_distribution(db)


@router.get("/forecasts")
def get_forecasts(
    days_ahead: int = Query(90, ge=1, le=365),
    product: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    from app.services.forecasting_service import get_upcoming_opportunities
    return get_upcoming_opportunities(db, days_ahead=days_ahead, product=product, region=region)


@router.get("/competitive/market-share-trends")
def get_market_share_trends(
    product: Optional[str] = Query(None),
    months: int = Query(24, ge=1, le=60),
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    from app.services.competitive_intel_service import get_market_share_trends as _get
    return _get(db, product=product, months=months)


@router.get("/competitive/supplier-win-rates")
def get_supplier_win_rates(
    supplier: Optional[str] = Query(None),
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    from app.services.competitive_intel_service import get_supplier_win_rates as _get
    return _get(db, supplier=supplier)


@router.get("/competitive/new-entrants")
def get_new_entrants(
    lookback_months: int = Query(6, ge=1, le=24),
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    from app.services.competitive_intel_service import detect_new_entrants
    return detect_new_entrants(db, lookback_months=lookback_months)


@router.get("/competitive/price-positioning")
def get_price_positioning(
    product: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    from app.services.competitive_intel_service import get_price_positioning as _get
    return _get(db, product=product, supplier=supplier)


@router.get("/regional-heatmap")
def get_regional_heatmap(
    product: Optional[str] = Query(None),
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    return svc.get_regional_demand_heatmap(db, product=product)


@router.post("/export")
def export_csv(
    dataset: str = Query(..., description="prices|market-share|procurement|trends|institutions|regions"),
    market: Optional[str] = Query(None),
    drug: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    org=Depends(get_api_key),
    db: Session = Depends(get_db),
):
    data_map = {
        "market-share": lambda: svc.get_market_share(db, market=market),
        "procurement": lambda: svc.get_top_institutions(db, limit=limit, region=region),
        "trends": lambda: svc.get_sales_trends(db, drug=drug),
        "institutions": lambda: svc.get_top_institutions(db, limit=limit, region=region),
        "regions": lambda: svc.get_regional_distribution(db),
    }

    if dataset == "prices":
        from app.models.price import Price
        from app.models.medication import Medication
        from app.models.pharmacy import Pharmacy
        rows = db.query(Price, Medication, Pharmacy).join(
            Medication, Price.medication_id == Medication.id
        ).join(Pharmacy, Price.pharmacy_id == Pharmacy.id).limit(limit).all()
        data = [
            {
                "medication": med.name,
                "active_ingredient": med.active_ingredient,
                "pharmacy": pharm.name,
                "chain": pharm.chain,
                "price": p.price,
                "in_stock": p.in_stock,
            }
            for p, med, pharm in rows
        ]
    elif dataset in data_map:
        data = data_map[dataset]()
    else:
        return {"error": f"Unknown dataset: {dataset}"}

    if not data:
        return {"error": "No data found"}

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={dataset}.csv"},
    )
