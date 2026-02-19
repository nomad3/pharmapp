from pydantic import BaseModel

class PharmacyOut(BaseModel):
    id: str
    chain: str
    name: str
    address: str
    comuna: str
    phone: str | None
    hours: str | None
    distance_km: float | None = None

    class Config:
        from_attributes = True
