import asyncio

import httpx
from app.scrapers.base import BaseScraper, ScrapedProduct


class CruzVerdeScraper(BaseScraper):
    CHAIN = "cruz_verde"
    API_URL = "https://beta.cruzverde.cl/s/Chile/dw/shop/v19_1/product_search"
    CLIENT_ID = "c19ce24d-1677-4754-b9f7-c193997c5a92"
    RATE_LIMIT_DELAY = 2.0
    CATALOG_PAGE_SIZE = 200

    def _parse_hit(self, hit: dict) -> ScrapedProduct | None:
        """Parse a single SFCC OCAPI hit into a ScrapedProduct."""
        price = hit.get("price", 0)
        if price <= 0:
            return None

        image = hit.get("image")
        image_url = image.get("link", "") if isinstance(image, dict) else ""

        return ScrapedProduct(
            chain=self.CHAIN,
            name=hit.get("product_name", ""),
            lab=hit.get("c_brand", "") or hit.get("brand", ""),
            price=price,
            in_stock=hit.get("orderable", False),
            source_url=f"https://www.cruzverde.cl/{hit.get('product_id', '')}",
            sku=hit.get("product_id", ""),
            image_url=image_url,
        )

    async def search(self, query: str) -> list[ScrapedProduct]:
        results = []
        async with httpx.AsyncClient(timeout=30) as client:
            try:
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
            except httpx.HTTPStatusError:
                return []
            data = self._safe_json(resp)
            if not data:
                return []
            for hit in data.get("hits", []):
                try:
                    product = self._parse_hit(hit)
                    if product:
                        results.append(product)
                except Exception as e:
                    self.logger.warning("Skipping malformed Cruz Verde hit: %s", e)
        return results

    async def browse_catalog(self) -> list[ScrapedProduct]:
        """Browse the entire Medicamentos category via SFCC OCAPI pagination."""
        results = []
        seen_ids: set[str] = set()

        async with httpx.AsyncClient(timeout=30) as client:
            start = 0
            total = None

            while True:
                try:
                    resp = await self._get_with_retry(
                        client,
                        self.API_URL,
                        params={
                            "refine_1": "cgid=medicamentos",
                            "client_id": self.CLIENT_ID,
                            "count": self.CATALOG_PAGE_SIZE,
                            "start": start,
                            "expand": "prices,availability,images",
                        },
                    )
                    data = self._safe_json(resp)
                    if not data:
                        break

                    if total is None:
                        total = data.get("total", 0)
                        self.logger.info("Cruz Verde catalog: %d total products", total)

                    hits = data.get("hits", [])
                    if not hits:
                        break

                    page_count = 0
                    for hit in hits:
                        try:
                            pid = hit.get("product_id", "")
                            if pid in seen_ids:
                                continue
                            seen_ids.add(pid)

                            product = self._parse_hit(hit)
                            if product:
                                results.append(product)
                                page_count += 1
                        except Exception as e:
                            self.logger.warning("Skipping malformed Cruz Verde hit: %s", e)

                    self.logger.info(
                        "Cruz Verde catalog offset %d: %d products (total: %d/%d)",
                        start, page_count, len(results), total or 0,
                    )

                except httpx.HTTPStatusError as e:
                    self.errors.append(f"Cruz Verde catalog offset {start}: HTTP {e.response.status_code}")
                    self.logger.error("HTTP error at offset %d: %s", start, e)
                    break
                except Exception as e:
                    self.errors.append(f"Cruz Verde catalog offset {start}: {e}")
                    self.logger.error("Error at offset %d: %s", start, e)
                    break

                start += self.CATALOG_PAGE_SIZE
                if total and start >= total:
                    break

                await asyncio.sleep(self.RATE_LIMIT_DELAY)

        self.logger.info(
            "Cruz Verde catalog complete: %d products, %d errors",
            len(results), len(self.errors),
        )
        self.results = results
        return results
