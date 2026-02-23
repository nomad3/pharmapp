import httpx
from app.scrapers.base import BaseScraper, ScrapedProduct


class CruzVerdeScraper(BaseScraper):
    CHAIN = "cruz_verde"
    API_URL = "https://beta.cruzverde.cl/s/Chile/dw/shop/v19_1/product_search"
    CLIENT_ID = "c19ce24d-1677-4754-b9f7-c193997c5a92"
    RATE_LIMIT_DELAY = 2.0

    async def search(self, query: str) -> list[ScrapedProduct]:
        results = []
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await self._get_with_retry(
                client,
                self.API_URL,
                params={
                    "q": query,
                    "client_id": self.CLIENT_ID,
                    "count": 25,
                    "expand": "prices,availability,images",
                },
            )
            data = resp.json()
            for hit in data.get("hits", []):
                price = hit.get("price", 0)
                if price <= 0:
                    continue

                image = hit.get("image")
                image_url = image.get("link", "") if isinstance(image, dict) else ""

                results.append(ScrapedProduct(
                    chain=self.CHAIN,
                    name=hit.get("product_name", ""),
                    lab=hit.get("c_brand", "") or hit.get("brand", ""),
                    price=price,
                    in_stock=hit.get("orderable", False),
                    source_url=f"https://www.cruzverde.cl/{hit.get('product_id', '')}",
                    sku=hit.get("product_id", ""),
                    image_url=image_url,
                ))
        return results
