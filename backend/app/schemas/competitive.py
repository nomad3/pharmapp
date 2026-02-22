from pydantic import BaseModel


class MarketShareTrend(BaseModel):
    period: str
    provider: str
    units: int
    revenue: float


class SupplierWinRate(BaseModel):
    supplier: str
    total_bids: int
    wins: int
    win_rate_pct: float


class NewEntrant(BaseModel):
    supplier: str
    first_seen: str | None = None
    total_units: int
    total_revenue: float


class PricePosition(BaseModel):
    supplier: str
    avg_price: float
    min_price: float
    max_price: float
    vs_market_pct: float
    transaction_count: int
    market_avg: float
