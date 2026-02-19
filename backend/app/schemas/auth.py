from pydantic import BaseModel

class OtpRequest(BaseModel):
    phone_number: str

class OtpVerify(BaseModel):
    phone_number: str
    code: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: str
    phone_number: str
    name: str | None
    comuna: str | None

    class Config:
        from_attributes = True
