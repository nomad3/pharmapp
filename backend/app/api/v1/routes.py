from fastapi import APIRouter
from app.api.v1 import auth, medications, pharmacies, prices

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(medications.router)
api_router.include_router(pharmacies.router)
api_router.include_router(prices.router)
