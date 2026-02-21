from pydantic import BaseModel
from typing import Optional


class DashboardSummary(BaseModel):
    # BMS
    bms_distribution_records: int = 0
    bms_purchase_orders: int = 0
    bms_adjudications: int = 0
    bms_institutions: int = 0
    bms_total_revenue: float = 0
    # Cenabast
    cenabast_products: int = 0
    cenabast_invoices: int = 0
    cenabast_total_revenue: float = 0
    # Combined
    total_drugs: int = 0


class MarketShareItem(BaseModel):
    drug: str
    market: Optional[str] = None
    bms_units: int = 0
    competition_units: int = 0
    bms_share_pct: float = 0


class SalesTrendItem(BaseModel):
    period: str
    bms_revenue: float = 0
    competition_revenue: float = 0
    total_units: int = 0


class TopInstitutionItem(BaseModel):
    rut: Optional[str] = None
    razon_social: Optional[str] = None
    region: Optional[str] = None
    total_units: int = 0
    total_revenue: float = 0


class RegionalDistribution(BaseModel):
    region: str
    total_units: int = 0
    total_revenue: float = 0
    institution_count: int = 0


class DrugPriceComparison(BaseModel):
    drug: str
    avg_price_bms: Optional[float] = None
    avg_price_competition: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None


class CenabastTrendItem(BaseModel):
    period: str
    total_revenue: float = 0
    total_units: int = 0
    invoice_count: int = 0


class CenabastTopPharmacy(BaseModel):
    rut: Optional[str] = None
    nombre: Optional[str] = None
    comuna: Optional[str] = None
    region: Optional[str] = None
    total_units: int = 0
    total_revenue: float = 0


class CenabastTopProduct(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    total_units: int = 0
    total_revenue: float = 0
    precio_maximo: Optional[float] = None


class CenabastRegionalItem(BaseModel):
    region: str
    total_units: int = 0
    total_revenue: float = 0
    pharmacy_count: int = 0
