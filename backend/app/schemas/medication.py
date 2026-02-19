from pydantic import BaseModel

class MedicationOut(BaseModel):
    id: str
    name: str
    active_ingredient: str | None
    dosage: str | None
    form: str | None
    lab: str | None
    isp_registry_number: str | None
    requires_prescription: bool

    class Config:
        from_attributes = True
