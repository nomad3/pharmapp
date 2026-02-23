import uuid
from pydantic import BaseModel


class AddressCreate(BaseModel):
    label: str = "home"
    address: str
    comuna: str
    instructions: str | None = None


class AddressOut(BaseModel):
    id: uuid.UUID
    label: str
    address: str
    comuna: str
    instructions: str | None

    class Config:
        from_attributes = True
