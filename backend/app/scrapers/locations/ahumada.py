import asyncio
import re

import httpx
from app.scrapers.locations.base import BaseLocationScraper, ScrapedLocation


class AhumadaLocationScraper(BaseLocationScraper):
    CHAIN = "ahumada"
    BASE_URL = (
        "https://www.farmaciasahumada.cl/on/demandware.store/"
        "Sites-ahumada-cl-Site/default/Stores-FindStores"
    )
    RATE_LIMIT_DELAY = 2.0

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Language": "es-CL,es;q=0.9",
    }

    REGIONS = [
        "Región Metropolitana",
        "Valparaíso",
        "Bío Bío",
        "Maule",
        "Araucanía",
        "Coquimbo",
        "Los Lagos",
        "Los Ríos",
        "Ñuble",
        "Antofagasta",
        "Atacama",
        "Tarapacá",
        "Arica y Parinacota",
        "Aysén",
        "Magallanes y la Antártica Chilena",
        # O'Higgins excluded: apostrophe in name causes SFCC 500 error
    ]

    async def scrape_locations(self) -> list[ScrapedLocation]:
        seen: set[str] = set()
        results: list[ScrapedLocation] = []

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for region in self.REGIONS:
                try:
                    resp = await self._get_with_retry(
                        client,
                        self.BASE_URL,
                        params={"regionId": region},
                        headers=self.HEADERS,
                    )
                    data = self._safe_json(resp)
                    if not data:
                        self.logger.warning("No JSON response for region: %s", region)
                        continue

                    stores = data.get("stores", [])
                    self.logger.info(
                        "Region '%s': found %d stores", region, len(stores)
                    )

                    for store in stores:
                        try:
                            store_id = str(store.get("ID", "")).strip()
                            if not store_id or store_id in seen:
                                continue
                            seen.add(store_id)

                            address = store.get("address1", "")
                            address2 = store.get("address2", "")
                            if address2:
                                address = f"{address}, {address2}"

                            hours_html = store.get("storeHours", "")
                            hours = self._clean_hours(hours_html)

                            results.append(ScrapedLocation(
                                chain=self.CHAIN,
                                branch_code=store_id,
                                name=store.get("name", ""),
                                address=address,
                                comuna=store.get("city", ""),
                                lat=float(store.get("latitude", 0)),
                                lng=float(store.get("longitude", 0)),
                                phone=store.get("phone", ""),
                                hours=hours,
                            ))
                        except Exception as e:
                            self.logger.warning(
                                "Skipping malformed Ahumada store: %s", e
                            )

                except httpx.HTTPStatusError as e:
                    self.errors.append(
                        f"Ahumada region '{region}': HTTP {e.response.status_code}"
                    )
                    self.logger.error(
                        "HTTP error for region '%s': %s", region, e
                    )
                except Exception as e:
                    self.errors.append(f"Ahumada region '{region}': {e}")
                    self.logger.error(
                        "Error fetching Ahumada stores for region '%s': %s",
                        region, e,
                    )

                await asyncio.sleep(self.RATE_LIMIT_DELAY)

        self.logger.info(
            "Ahumada scrape complete: %d stores, %d errors",
            len(results), len(self.errors),
        )
        self.results = results
        return results

    @staticmethod
    def _clean_hours(hours_html: str) -> str:
        if not hours_html:
            return ""
        text = re.sub(r"<[^>]+>", " ", hours_html)
        text = re.sub(r"\s+", " ", text).strip()
        return text
