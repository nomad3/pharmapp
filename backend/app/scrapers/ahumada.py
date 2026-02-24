import asyncio
import re

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, ScrapedProduct


class AhumadaScraper(BaseScraper):
    CHAIN = "ahumada"
    BASE_URL = "https://www.farmaciasahumada.cl"
    RATE_LIMIT_DELAY = 3.0
    CATALOG_PAGE_SIZE = 24

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "es-CL,es;q=0.9",
    }

    # Fallback regex for when BeautifulSoup parsing finds nothing
    _TILE_RE = re.compile(
        r'data-pid="([^"]+)"[^>]*>.*?'
        r'class="[^"]*product-name[^"]*"[^>]*>([^<]+)<.*?'
        r'class="[^"]*sales[^"]*"[^>]*>\s*\$\s*([\d.,]+)',
        re.DOTALL,
    )

    _PRICE_RE = re.compile(r'[\d.,]+')

    async def search(self, query: str) -> list[ScrapedProduct]:
        results = []
        source_url = f"{self.BASE_URL}/search?q={query}"
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            try:
                resp = await self._get_with_retry(
                    client,
                    f"{self.BASE_URL}/search",
                    params={"q": query, "sz": 24},
                    headers=self.HEADERS,
                )
                html = resp.text

                # Primary: BeautifulSoup parsing
                results = self._parse_with_bs4(html, source_url)

                # Fallback: regex if BS4 found nothing
                if not results:
                    self.logger.info("BS4 found 0 products for '%s', falling back to regex", query)
                    results = self._parse_with_regex(html, source_url)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    self.logger.warning("Ahumada blocked by Cloudflare for query '%s' — skipping", query)
                else:
                    raise
        return results

    async def browse_catalog(self) -> list[ScrapedProduct]:
        """Browse the entire Medicamentos category via SFCC Search-UpdateGrid pagination."""
        results = []
        seen_pids: set[str] = set()

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            start = 0
            consecutive_empty = 0

            while consecutive_empty < 2:
                try:
                    url = (
                        f"{self.BASE_URL}/on/demandware.store/"
                        f"Sites-ahumada-cl-Site/default/Search-UpdateGrid"
                    )
                    resp = await self._get_with_retry(
                        client,
                        url,
                        params={
                            "cgid": "medicamentos",
                            "start": start,
                            "sz": self.CATALOG_PAGE_SIZE,
                        },
                        headers=self.HEADERS,
                    )
                    html = resp.text
                    source_url = f"{self.BASE_URL}/medicamentos?start={start}"

                    page_products = self._parse_with_bs4(html, source_url)

                    if not page_products:
                        consecutive_empty += 1
                        self.logger.info(
                            "Ahumada catalog offset %d: 0 products (empty: %d/2)",
                            start, consecutive_empty,
                        )
                        start += self.CATALOG_PAGE_SIZE
                        await asyncio.sleep(self.RATE_LIMIT_DELAY)
                        continue

                    consecutive_empty = 0
                    page_count = 0
                    for p in page_products:
                        if p.sku and p.sku not in seen_pids:
                            seen_pids.add(p.sku)
                            results.append(p)
                            page_count += 1

                    self.logger.info(
                        "Ahumada catalog offset %d: %d new products (total: %d)",
                        start, page_count, len(results),
                    )

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 403:
                        self.logger.warning(
                            "Ahumada Cloudflare block at offset %d — stopping", start
                        )
                        self.errors.append(f"Ahumada catalog offset {start}: Cloudflare 403")
                        break
                    self.errors.append(f"Ahumada catalog offset {start}: HTTP {e.response.status_code}")
                    self.logger.error("HTTP error at offset %d: %s", start, e)
                    break
                except Exception as e:
                    self.errors.append(f"Ahumada catalog offset {start}: {e}")
                    self.logger.error("Error at offset %d: %s", start, e)
                    break

                start += self.CATALOG_PAGE_SIZE
                await asyncio.sleep(self.RATE_LIMIT_DELAY)

        self.logger.info(
            "Ahumada catalog complete: %d products, %d errors",
            len(results), len(self.errors),
        )
        self.results = results
        return results

    def _parse_with_bs4(self, html: str, source_url: str) -> list[ScrapedProduct]:
        """Parse product tiles from SFCC HTML using BeautifulSoup."""
        results = []
        soup = BeautifulSoup(html, "html.parser")

        # SFCC product tiles carry a data-pid attribute
        tiles = soup.select("[data-pid]")
        if not tiles:
            tiles = soup.select(".product-tile")

        for tile in tiles:
            try:
                # --- SKU / PID ---
                pid = tile.get("data-pid", "")

                # --- Product name ---
                name_el = (
                    tile.select_one(".pdp-link a")
                    or tile.select_one(".pdp-link")
                    or tile.select_one(".product-name a")
                    or tile.select_one(".product-name")
                )
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)
                if not name:
                    continue

                # --- Price ---
                price_el = (
                    tile.select_one(".sales .value")
                    or tile.select_one(".price .sales .value")
                    or tile.select_one(".price .sales")
                    or tile.select_one(".sales")
                )
                if not price_el:
                    continue

                price_text = price_el.get("content") or price_el.get_text(strip=True)
                price = self._extract_price(price_text)
                if price is None or price <= 0:
                    continue

                # --- Original price (crossed-out / list price) ---
                original_price = None
                orig_el = tile.select_one(".strike-through .value") or tile.select_one(".list-price .value")
                if orig_el:
                    orig_text = orig_el.get("content") or orig_el.get_text(strip=True)
                    original_price = self._extract_price(orig_text)

                # --- Image ---
                img_el = tile.select_one("img.tile-image") or tile.select_one(".image-container img")
                image_url = None
                if img_el:
                    image_url = img_el.get("src") or img_el.get("data-src")

                # --- Brand ---
                brand = None
                brand_el = tile.select_one(".product-brand") or tile.select_one(".brand-name")
                if brand_el:
                    brand = brand_el.get_text(strip=True) or None

                results.append(ScrapedProduct(
                    chain=self.CHAIN,
                    name=name,
                    lab=brand,
                    price=price,
                    original_price=original_price,
                    in_stock=True,
                    source_url=source_url,
                    sku=pid,
                    image_url=image_url,
                ))
            except Exception as e:
                self.logger.warning("Skipping malformed Ahumada tile: %s", e)

        return results

    def _parse_with_regex(self, html: str, source_url: str) -> list[ScrapedProduct]:
        """Legacy regex fallback for when BS4 parsing returns nothing."""
        results = []
        for pid, name, price_str in self._TILE_RE.findall(html):
            try:
                price = float(price_str.replace(".", "").replace(",", "."))
                if price <= 0:
                    continue
                results.append(ScrapedProduct(
                    chain=self.CHAIN,
                    name=name.strip(),
                    price=price,
                    in_stock=True,
                    source_url=source_url,
                    sku=pid,
                ))
            except (ValueError, TypeError) as e:
                self.logger.warning("Regex fallback skipping pid %s: %s", pid, e)
        return results

    def _extract_price(self, text: str) -> float | None:
        """Extract a numeric price from text like '$731', '$1.290', '$470 x Comp.'."""
        if not text:
            return None
        # Try to parse as plain float first (for content attributes like "731.0")
        try:
            return float(text)
        except (ValueError, TypeError):
            pass
        # Extract digits and separators from CLP formatted text
        match = self._PRICE_RE.search(text)
        if not match:
            return None
        try:
            raw = match.group(0)
            # CLP uses dots as thousands separator: "1.290" -> 1290
            return float(raw.replace(".", "").replace(",", "."))
        except (ValueError, TypeError):
            return None
