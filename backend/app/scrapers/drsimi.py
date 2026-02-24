import asyncio
import re

import httpx
from app.scrapers.base import BaseScraper, ScrapedProduct


class DrSimiScraper(BaseScraper):
    CHAIN = "dr_simi"
    BASE_URL = "https://www.drsimi.cl"
    RATE_LIMIT_DELAY = 1.5
    CATALOG_PAGE_SIZE = 50
    CATEGORY_ID = 7  # "Medicamento" category

    def _parse_vtex_product(self, product: dict) -> list[ScrapedProduct]:
        """Parse a VTEX product into one or more ScrapedProduct (one per item/SKU)."""
        results = []
        try:
            principio = product.get("Principio Activo")
            active_ingredient = principio[0] if isinstance(principio, list) and principio else None

            receta = product.get("Receta Medica")
            needs_rx = receta[0] != "No" if isinstance(receta, list) and receta else False

            for item in product.get("items", []):
                sellers = item.get("sellers") or [{}]
                offer = sellers[0].get("commertialOffer", {})
                price = offer.get("Price", 0)
                list_price = offer.get("ListPrice", 0)
                available = offer.get("AvailableQuantity", 0) > 0
                if price <= 0:
                    continue

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
        except Exception as e:
            self.logger.warning("Skipping malformed Dr. Simi product: %s", e)
        return results

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
            data = self._safe_json(resp)
            if not data:
                return []
            for product in data:
                results.extend(self._parse_vtex_product(product))
        return results

    async def browse_catalog(self) -> list[ScrapedProduct]:
        """Browse the entire Medicamento category via VTEX pagination."""
        results = []
        seen_skus: set[str] = set()

        async with httpx.AsyncClient(timeout=30) as client:
            start = 0
            total = None

            while True:
                end = start + self.CATALOG_PAGE_SIZE - 1
                try:
                    resp = await self._get_with_retry(
                        client,
                        f"{self.BASE_URL}/api/catalog_system/pub/products/search",
                        params={
                            "fq": f"C:{self.CATEGORY_ID}",
                            "_from": start,
                            "_to": end,
                        },
                    )

                    # Parse total from resources header: "0-49/785"
                    if total is None:
                        resources = resp.headers.get("resources", "")
                        match = re.search(r"/(\d+)", resources)
                        if match:
                            total = int(match.group(1))
                            self.logger.info("Dr. Simi catalog: %d total products", total)

                    data = self._safe_json(resp)
                    if not data or not isinstance(data, list) or len(data) == 0:
                        break

                    page_count = 0
                    for product in data:
                        for p in self._parse_vtex_product(product):
                            if p.sku not in seen_skus:
                                seen_skus.add(p.sku)
                                results.append(p)
                                page_count += 1

                    self.logger.info(
                        "Dr. Simi catalog %d-%d: %d products (total: %d)",
                        start, end, page_count, len(results),
                    )

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 400:
                        self.logger.info("Dr. Simi catalog: 400 at offset %d, stopping", start)
                        break
                    self.errors.append(f"Dr. Simi catalog {start}-{end}: HTTP {e.response.status_code}")
                    self.logger.error("HTTP error at offset %d: %s", start, e)
                    break
                except Exception as e:
                    self.errors.append(f"Dr. Simi catalog {start}-{end}: {e}")
                    self.logger.error("Error at offset %d: %s", start, e)
                    break

                start += self.CATALOG_PAGE_SIZE
                if total and start >= total:
                    break

                await asyncio.sleep(self.RATE_LIMIT_DELAY)

        self.logger.info(
            "Dr. Simi catalog complete: %d products, %d errors",
            len(results), len(self.errors),
        )
        self.results = results
        return results
