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


class DrSimiLocationScraper(BaseLocationScraper):
    CHAIN = "dr_simi"
    BASE_URL = "https://www.drsimi.cl"
    RATE_LIMIT_DELAY = 1.5

    async def scrape_locations(self) -> list[ScrapedLocation]:
        seen = set()
        results = []
        async with httpx.AsyncClient(timeout=30) as client:
            for lat, lng in GEO_SEEDS:
                try:
                    resp = await self._get_with_retry(
                        client,
                        f"{self.BASE_URL}/api/checkout/pub/pickup-points",
                        params={"geoCoordinates": f"{lng};{lat}"},
                    )
                    data = self._safe_json(resp)
                    if not data:
                        continue
                    for item in data if isinstance(data, list) else data.get("items", data.get("pickupPoints", [])):
                        try:
                            # VTEX pickup point structure varies; handle both formats
                            if isinstance(item, dict) and "pickupPoint" in item:
                                pp = item["pickupPoint"]
                            else:
                                pp = item

                            pickup_id = pp.get("id", "")
                            if not pickup_id or pickup_id in seen:
                                continue
                            seen.add(pickup_id)

                            addr = pp.get("address", {})
                            geo = addr.get("geoCoordinates", [0, 0])
                            # VTEX geoCoordinates: [longitude, latitude]
                            p_lng = geo[0] if len(geo) > 0 else 0
                            p_lat = geo[1] if len(geo) > 1 else 0

                            hours_list = pp.get("businessHours", [])
                            hours_str = self._format_hours(hours_list)

                            results.append(ScrapedLocation(
                                chain=self.CHAIN,
                                branch_code=pickup_id,
                                name=pp.get("friendlyName", pp.get("name", "")),
                                address=f"{addr.get('street', '')} {addr.get('number', '')}".strip(),
                                comuna=addr.get('city', '') or addr.get('neighborhood', ''),
                                lat=p_lat,
                                lng=p_lng,
                                phone=addr.get('phone', '') or '',
                                hours=hours_str,
                            ))
                        except Exception as e:
                            self.logger.warning("Skipping malformed Dr. Simi pickup point: %s", e)
                except Exception as e:
                    self.errors.append(f"Dr. Simi locations seed ({lat},{lng}): {e}")
                    self.logger.error("Error fetching Dr. Simi locations for (%s,%s): %s", lat, lng, e)

                await asyncio.sleep(self.RATE_LIMIT_DELAY)

        self.results = results
        return results

    @staticmethod
    def _format_hours(business_hours: list) -> str:
        if not business_hours:
            return ""
        parts = []
        days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        for bh in business_hours:
            day_idx = bh.get("DayOfWeek", 0)
            day_name = days[day_idx] if 0 <= day_idx < len(days) else str(day_idx)
            open_t = bh.get("OpeningTime", "")
            close_t = bh.get("ClosingTime", "")
            if open_t and close_t:
                parts.append(f"{day_name} {open_t[:5]}-{close_t[:5]}")
        return ", ".join(parts)
