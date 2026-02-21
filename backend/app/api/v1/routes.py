from fastapi import APIRouter
from app.api.v1 import auth, medications, pharmacies, prices, orders, webhooks, favorites, search_history, analytics

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

@api_router.post("/admin/trigger-scraping")
async def trigger_scraping():
    from app.tasks.scraping import trigger_all_scrapers
    return await trigger_all_scrapers()
