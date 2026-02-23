import httpx
from app.scrapers.base import BaseScraper, ScrapedProduct


class SalcobrandScraper(BaseScraper):
    CHAIN = "salcobrand"
    ALGOLIA_URL = "https://GM3RP06HJG-dsn.algolia.net/1/indexes/sb_variant_production/query"
    ALGOLIA_APP_ID = "GM3RP06HJG"
    ALGOLIA_API_KEY = "0259fe250b3be4b1326eb85e47aa7d81"
    RATE_LIMIT_DELAY = 1.5

    async def search(self, query: str) -> list[ScrapedProduct]:
        results = []
        headers = {
            "X-Algolia-Application-Id": self.ALGOLIA_APP_ID,
            "X-Algolia-API-Key": self.ALGOLIA_API_KEY,
            "Referer": "https://salcobrand.cl/",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await self._post_with_retry(
                client,
                self.ALGOLIA_URL,
                headers=headers,
                json={"params": f"query={query}&hitsPerPage=50"},
            )
            data = resp.json()
            for hit in data.get("hits", []):
                price = hit.get("price", 0) or hit.get("sale_price", 0)
                if price <= 0:
                    continue

                compare_price = hit.get("compare_at_price", 0)
                slug = hit.get("slug", hit.get("objectID", ""))

                results.append(ScrapedProduct(
                    chain=self.CHAIN,
                    name=hit.get("name", "") or hit.get("title", ""),
                    lab=hit.get("laboratory", "") or hit.get("brand", ""),
                    price=price,
                    original_price=compare_price if compare_price and compare_price > price else None,
                    in_stock=hit.get("in_stock", True),
                    source_url=f"https://salcobrand.cl/product/{slug}",
                    sku=str(hit.get("objectID", "")),
                    requires_prescription=bool(hit.get("recipe") or hit.get("requires_prescription")),
                ))
        return results
