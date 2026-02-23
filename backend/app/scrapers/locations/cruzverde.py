import asyncio

import httpx
from app.scrapers.locations.base import BaseLocationScraper, ScrapedLocation


GEO_SEEDS = [
    (-33.4489, -70.6693),   # Santiago Centro
    (-33.4017, -70.5726),   # Las Condes / Providencia
    (-33.5017, -70.7614),   # Maipú
    (-33.0153, -71.5509),   # Viña del Mar
    (-33.0472, -71.6127),   # Valparaíso
    (-36.8201, -73.0440),   # Concepción
    (-29.9511, -71.3436),   # La Serena
    (-38.7359, -72.5904),   # Temuco
    (-39.8142, -73.2459),   # Valdivia
    (-53.1548, -70.9113),   # Punta Arenas
    (-23.6345, -70.3860),   # Antofagasta
    (-20.2133, -70.1503),   # Iquique
]


class CruzVerdeLocationScraper(BaseLocationScraper):
    CHAIN = "cruz_verde"
    API_URL = "https://beta.cruzverde.cl/s/Chile/dw/shop/v19_1/stores"
    CLIENT_ID = "c19ce24d-1677-4754-b9f7-c193997c5a92"
    RATE_LIMIT_DELAY = 2.0

    async def scrape_locations(self) -> list[ScrapedLocation]:
        seen = set()
        results = []
        async with httpx.AsyncClient(timeout=30) as client:
            for lat, lng in GEO_SEEDS:
                try:
                    resp = await self._get_with_retry(
                        client,
                        self.API_URL,
                        params={
                            "latitude": lat,
                            "longitude": lng,
                            "count": 200,
                            "client_id": self.CLIENT_ID,
                        },
                    )
                    data = self._safe_json(resp)
                    if not data:
                        continue
                    for store in data.get("data", data.get("stores", [])):
                        try:
                            store_id = store.get("id", "")
                            if not store_id or store_id in seen:
                                continue
                            seen.add(store_id)

                            results.append(ScrapedLocation(
                                chain=self.CHAIN,
                                branch_code=store_id,
                                name=store.get("name", ""),
                                address=f"{store.get('address1', '')} {store.get('address2', '')}".strip(),
                                comuna=store.get('city', ''),
                                lat=store.get("latitude", 0),
                                lng=store.get("longitude", 0),
                                phone=store.get("phone", ""),
                                hours=self._format_hours(store.get("store_hours", "")),
                            ))
                        except Exception as e:
                            self.logger.warning("Skipping malformed Cruz Verde store: %s", e)
                except Exception as e:
                    self.errors.append(f"Cruz Verde locations seed ({lat},{lng}): {e}")
                    self.logger.error("Error fetching Cruz Verde locations for (%s,%s): %s", lat, lng, e)

                await asyncio.sleep(self.RATE_LIMIT_DELAY)

        self.results = results
        return results

    @staticmethod
    def _format_hours(store_hours) -> str:
        if isinstance(store_hours, str):
            return store_hours
        if isinstance(store_hours, dict):
            parts = []
            for day, hours in store_hours.items():
                parts.append(f"{day}: {hours}")
            return ", ".join(parts)
        return ""
