from pydantic import BaseModel

class OrderItemCreate(BaseModel):
    medication_id: str
    price_id: str
    quantity: int = 1

class OrderCreate(BaseModel):
    pharmacy_id: str
    items: list[OrderItemCreate]
    payment_provider: str
    delivery_address_id: str | None = None

class OrderOut(BaseModel):
    id: str
    status: str
    payment_provider: str | None
    payment_url: str | None
    total: float
    created_at: str

    class Config:
        from_attributes = True
