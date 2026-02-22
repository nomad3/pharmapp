from pydantic import BaseModel


class CenabastCostInfo(BaseModel):
    avg_cenabast_cost: float
    precio_maximo_publico: float | None = None
    invoice_count: int


class MarkupInfo(BaseModel):
    pharmacy_name: str
    chain: str
    retail_price: float
    cenabast_cost: float
    markup_pct: float
    is_precio_justo: bool


class OverpricedMedication(BaseModel):
    medication_id: str
    medication_name: str
    active_ingredient: str | None = None
    avg_retail: float
    cenabast_cost: float
    markup_pct: float


class PharmacyTransparencyIndex(BaseModel):
    chain: str
    avg_markup_pct: float
    medication_count: int
    transparency_score: float


class TransparencyStats(BaseModel):
    total_medications: int
    medications_with_transparency: int
    avg_cenabast_cost: float
    avg_retail_price: float
    avg_markup_pct: float


class TransparentPriceCompareItem(BaseModel):
    price: float
    in_stock: bool
    pharmacy: dict
    distance_km: float | None = None
    cenabast_cost: float | None = None
    markup_pct: float | None = None
    is_precio_justo: bool | None = None
