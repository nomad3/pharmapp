import asyncio

import httpx
from app.scrapers.base import BaseScraper, ScrapedProduct


class SalcobrandScraper(BaseScraper):
    CHAIN = "salcobrand"
    ALGOLIA_URL = "https://GM3RP06HJG-dsn.algolia.net/1/indexes/*/queries"
    ALGOLIA_APP_ID = "GM3RP06HJG"
    ALGOLIA_API_KEY = "0259fe250b3be4b1326eb85e47aa7d81"
    INDEX_NAME = "sb_variant_production"
    RATE_LIMIT_DELAY = 1.5

    def _algolia_headers(self) -> dict:
        return {
            "X-Algolia-Application-Id": self.ALGOLIA_APP_ID,
            "X-Algolia-API-Key": self.ALGOLIA_API_KEY,
            "Referer": "https://salcobrand.cl/",
            "Content-Type": "application/json",
        }

    def _parse_hit(self, hit: dict) -> ScrapedProduct | None:
        """Parse a single Algolia hit into a ScrapedProduct."""
        price = hit.get("normal_price", 0) or hit.get("sale_price", 0)
        if not price or price <= 0:
            return None

        compare_price = hit.get("compare_at_price") or hit.get("original_price")
        original_price = compare_price if compare_price and compare_price > price else None

        product_url = hit.get("product_url", "")
        if product_url and not product_url.startswith("http"):
            product_url = f"https://salcobrand.cl{product_url}"
        elif not product_url:
            slug = hit.get("slug", hit.get("objectID", ""))
            product_url = f"https://salcobrand.cl/product/{slug}"

        return ScrapedProduct(
            chain=self.CHAIN,
            name=hit.get("name", "") or hit.get("title", ""),
            lab=hit.get("brand", ""),
            price=price,
            original_price=original_price,
            in_stock=bool(hit.get("has_stock", True)),
            source_url=product_url,
            sku=str(hit.get("objectID", "")),
            image_url=hit.get("thumbnail_image_url", ""),
            requires_prescription=bool(hit.get("needs_recipe")),
        )

    async def search(self, query: str) -> list[ScrapedProduct]:
        results = []
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await self._post_with_retry(
                client,
                self.ALGOLIA_URL,
                headers=self._algolia_headers(),
                json={
                    "requests": [{
                        "indexName": self.INDEX_NAME,
                        "params": f"query={query}&hitsPerPage=50",
                    }]
                },
            )
            data = self._safe_json(resp)
            if not data:
                return []
            for hit in data.get("results", [{}])[0].get("hits", []):
                try:
                    product = self._parse_hit(hit)
                    if product:
                        results.append(product)
                except Exception as e:
                    self.logger.warning("Skipping malformed Salcobrand hit: %s", e)
        return results

    async def browse_catalog(self) -> list[ScrapedProduct]:
        """Browse the entire Medicamentos category via Algolia pagination."""
        results = []
        seen_ids: set[str] = set()

        async with httpx.AsyncClient(timeout=30) as client:
            page = 0
            nb_pages = 1  # will be updated from first response

            while page < nb_pages:
                try:
                    resp = await self._post_with_retry(
                        client,
                        self.ALGOLIA_URL,
                        headers=self._algolia_headers(),
                        json={
                            "requests": [{
                                "indexName": self.INDEX_NAME,
                                "params": (
                                    f"hitsPerPage=50&page={page}"
                                    f'&facetFilters=["product_categories.lvl0:Medicamentos"]'
                                ),
                            }]
                        },
                    )
                    data = self._safe_json(resp)
                    if not data:
                        break

                    result_data = data.get("results", [{}])[0]
                    nb_pages = result_data.get("nbPages", 0)
                    hits = result_data.get("hits", [])

                    if not hits:
                        break

                    page_count = 0
                    for hit in hits:
                        try:
                            oid = str(hit.get("objectID", ""))
                            if oid in seen_ids:
                                continue
                            seen_ids.add(oid)

                            product = self._parse_hit(hit)
                            if product:
                                results.append(product)
                                page_count += 1
                        except Exception as e:
                            self.logger.warning("Skipping malformed Salcobrand hit: %s", e)

                    self.logger.info(
                        "Salcobrand catalog page %d/%d: %d products (total: %d)",
                        page + 1, nb_pages, page_count, len(results),
                    )

                except httpx.HTTPStatusError as e:
                    self.errors.append(f"Salcobrand catalog page {page}: HTTP {e.response.status_code}")
                    self.logger.error("HTTP error on catalog page %d: %s", page, e)
                    break
                except Exception as e:
                    self.errors.append(f"Salcobrand catalog page {page}: {e}")
                    self.logger.error("Error on catalog page %d: %s", page, e)
                    break

                page += 1
                if page < nb_pages:
                    await asyncio.sleep(self.RATE_LIMIT_DELAY)

        self.logger.info(
            "Salcobrand catalog complete: %d products, %d errors",
            len(results), len(self.errors),
        )
        self.results = results
        return results
