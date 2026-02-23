import re

import httpx
from app.scrapers.base import BaseScraper, ScrapedProduct


class AhumadaScraper(BaseScraper):
    CHAIN = "ahumada"
    BASE_URL = "https://www.farmaciasahumada.cl"
    RATE_LIMIT_DELAY = 3.0

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "es-CL,es;q=0.9",
    }

    async def search(self, query: str) -> list[ScrapedProduct]:
        results = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            try:
                resp = await self._get_with_retry(
                    client,
                    f"{self.BASE_URL}/search",
                    params={"q": query, "sz": 24},
                    headers=self.HEADERS,
                )
                html = resp.text

                # Parse product tiles from SFCC HTML
                tiles = re.findall(
                    r'data-pid="([^"]+)"[^>]*>.*?'
                    r'class="[^"]*product-name[^"]*"[^>]*>([^<]+)<.*?'
                    r'class="[^"]*sales[^"]*"[^>]*>\s*\$\s*([\d.,]+)',
                    html,
                    re.DOTALL,
                )
                for pid, name, price_str in tiles:
                    price = float(price_str.replace(".", "").replace(",", "."))
                    if price <= 0:
                        continue
                    results.append(ScrapedProduct(
                        chain=self.CHAIN,
                        name=name.strip(),
                        price=price,
                        in_stock=True,
                        source_url=f"{self.BASE_URL}/search?q={query}",
                        sku=pid,
                    ))
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    self.logger.warning("Ahumada blocked by Cloudflare — skipping")
                else:
                    raise
        return results
