from pydantic import BaseModel


class TenderForecast(BaseModel):
    product: str
    institution_rut: str
    last_purchase_date: str
    predicted_next_date: str
    confidence_low: str
    confidence_high: str
    avg_quantity: int
    confidence_level: str
    purchase_count: int


class ForecastOpportunity(BaseModel):
    product: str
    institution_rut: str
    institution_name: str | None = None
    predicted_date: str
    days_until: int
    estimated_value: float
    confidence_level: str
    avg_quantity: int
