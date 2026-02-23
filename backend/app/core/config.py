from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/pharmapp"
    SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440
    OTP_EXPIRATION_MINUTES: int = 5

    # ServiceTsunami / OpenClaw
    SERVICETSUNAMI_API_URL: str = "http://localhost:8001"
    SERVICETSUNAMI_EMAIL: str = ""
    SERVICETSUNAMI_PASSWORD: str = ""
    SERVICETSUNAMI_AGENT_ID: str = ""

    # PharmApp webhook URL (registered with ServiceTsunami for incoming WhatsApp)
    PHARMAPP_WEBHOOK_URL: str = "http://localhost:8000/api/v1/webhooks/whatsapp"
    PHARMAPP_WEBHOOK_SECRET: str = ""

    # Payments
    MERCADOPAGO_ACCESS_TOKEN: str = ""
    TRANSBANK_COMMERCE_CODE: str = ""
    TRANSBANK_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""

    # Frontend URL (for payment redirect back URLs)
    FRONTEND_URL: str = "http://localhost:3000"

    # Stripe (monetization)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PRO: str = ""
    STRIPE_PRICE_ID_ENTERPRISE: str = ""
    STRIPE_PRICE_ID_PREMIUM: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
