from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/pharmapp"
    SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440
    OTP_EXPIRATION_MINUTES: int = 5
    SERVICETSUNAMI_API_URL: str = "http://localhost:8001"
    SERVICETSUNAMI_EMAIL: str = ""
    SERVICETSUNAMI_PASSWORD: str = ""
    MERCADOPAGO_ACCESS_TOKEN: str = ""
    TRANSBANK_COMMERCE_CODE: str = ""
    TRANSBANK_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
