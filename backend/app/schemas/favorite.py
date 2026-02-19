from pydantic import BaseModel

class FavoriteCreate(BaseModel):
    medication_id: str

class FavoriteOut(BaseModel):
    id: str
    medication_id: str
    created_at: str

    class Config:
        from_attributes = True
