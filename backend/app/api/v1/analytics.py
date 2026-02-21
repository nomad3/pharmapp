from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services import analytics as svc
from app.schemas.analytics import (
    DashboardSummary,
    MarketShareItem,
    SalesTrendItem,
    TopInstitutionItem,
    RegionalDistribution,
    DrugPriceComparison,
    CenabastTrendItem,
    CenabastTopPharmacy,
    CenabastTopProduct,
    CenabastRegionalItem,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    return svc.get_dashboard_summary(db)


# ── BMS endpoints ──────────────────────────────────────────────


@router.get("/market-share", response_model=list[MarketShareItem])
def market_share(market: Optional[str] = Query(None), db: Session = Depends(get_db)):
    return svc.get_market_share(db, market=market)


@router.get("/trends", response_model=list[SalesTrendItem])
def sales_trends(drug: Optional[str] = Query(None), db: Session = Depends(get_db)):
    return svc.get_sales_trends(db, drug=drug)


@router.get("/top-institutions", response_model=list[TopInstitutionItem])
def top_institutions(
    limit: int = Query(20, ge=1, le=100),
    region: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return svc.get_top_institutions(db, limit=limit, region=region)


@router.get("/regions", response_model=list[RegionalDistribution])
def regional_distribution(db: Session = Depends(get_db)):
    return svc.get_regional_distribution(db)


@router.get("/drug-prices", response_model=list[DrugPriceComparison])
def drug_prices(drug: Optional[str] = Query(None), db: Session = Depends(get_db)):
    return svc.get_drug_prices(db, drug=drug)


# ── Cenabast endpoints ─────────────────────────────────────────


@router.get("/cenabast/trends", response_model=list[CenabastTrendItem])
def cenabast_trends(product: Optional[str] = Query(None), db: Session = Depends(get_db)):
    return svc.get_cenabast_trends(db, product=product)


@router.get("/cenabast/top-pharmacies", response_model=list[CenabastTopPharmacy])
def cenabast_top_pharmacies(
    limit: int = Query(20, ge=1, le=100),
    region: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return svc.get_cenabast_top_pharmacies(db, limit=limit, region=region)


@router.get("/cenabast/top-products", response_model=list[CenabastTopProduct])
def cenabast_top_products(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return svc.get_cenabast_top_products(db, limit=limit)


@router.get("/cenabast/regions", response_model=list[CenabastRegionalItem])
def cenabast_regional(db: Session = Depends(get_db)):
    return svc.get_cenabast_regional(db)
