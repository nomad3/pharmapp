from fastapi import APIRouter
from app.api.v1 import (
    auth, medications, pharmacies, prices, orders, webhooks,
    favorites, search_history, analytics,
    billing, organizations, api_keys, data_api,
    commissions, premium,
    transparency, reports, gpo, adherence,
    scraping,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(medications.router)
api_router.include_router(pharmacies.router)
api_router.include_router(prices.router)
api_router.include_router(orders.router)
api_router.include_router(webhooks.router)
api_router.include_router(favorites.router)
api_router.include_router(search_history.router)
api_router.include_router(analytics.router)
# Monetization routers
api_router.include_router(billing.router)
api_router.include_router(organizations.router)
api_router.include_router(api_keys.router)
api_router.include_router(data_api.router)
api_router.include_router(commissions.router)
api_router.include_router(premium.router)
# Business model expansion routers
api_router.include_router(transparency.router)
api_router.include_router(reports.router)
api_router.include_router(gpo.router)
api_router.include_router(adherence.router)
# Scraping
api_router.include_router(scraping.router)
