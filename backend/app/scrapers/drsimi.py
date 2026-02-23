import httpx
from app.scrapers.base import BaseScraper, ScrapedProduct


class DrSimiScraper(BaseScraper):
    CHAIN = "dr_simi"
    BASE_URL = "https://www.drsimi.cl"
    RATE_LIMIT_DELAY = 1.5

    async def search(self, query: str) -> list[ScrapedProduct]:
        results = []
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await self._get_with_retry(
                    client,
                    f"{self.BASE_URL}/api/catalog_system/pub/products/search",
                    params={"ft": query, "_from": 0, "_to": 49},
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400:
                    return []  # VTEX returns 400 for queries it can't parse
                raise
            for product in resp.json():
                for item in product.get("items", []):
                    sellers = item.get("sellers") or [{}]
                    offer = sellers[0].get("commertialOffer", {})
                    price = offer.get("Price", 0)
                    list_price = offer.get("ListPrice", 0)
                    available = offer.get("AvailableQuantity", 0) > 0
                    if price <= 0:
                        continue

                    # Extract active ingredient from VTEX product specs
                    principio = product.get("Principio Activo")
                    active_ingredient = principio[0] if isinstance(principio, list) and principio else None

                    # Check prescription requirement
                    receta = product.get("Receta Medica")
                    needs_rx = receta[0] != "No" if isinstance(receta, list) and receta else False

                    images = item.get("images") or [{}]
                    results.append(ScrapedProduct(
                        chain=self.CHAIN,
                        name=product.get("productName", ""),
                        active_ingredient=active_ingredient,
                        lab=product.get("brand", ""),
                        price=price,
                        original_price=list_price if list_price > price else None,
                        in_stock=available,
                        source_url=f"{self.BASE_URL}{product.get('link', '')}",
                        sku=item.get("itemId", ""),
                        image_url=images[0].get("imageUrl", ""),
                        requires_prescription=needs_rx,
                    ))
        return results
