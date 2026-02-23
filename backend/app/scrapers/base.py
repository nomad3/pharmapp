import asyncio
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod

import httpx


@dataclass
class ScrapedProduct:
    chain: str
    name: str
    active_ingredient: str | None = None
    lab: str | None = None
    dosage: str | None = None
    form: str | None = None
    price: float = 0.0
    original_price: float | None = None
    in_stock: bool = True
    source_url: str = ""
    sku: str = ""
    image_url: str | None = None
    requires_prescription: bool = False


class BaseScraper(ABC):
    CHAIN: str = ""
    RATE_LIMIT_DELAY: float = 1.0
    MAX_RETRIES: int = 3

    def __init__(self):
        self.logger = logging.getLogger(f"scraper.{self.CHAIN}")
        self.results: list[ScrapedProduct] = []
        self.errors: list[str] = []

    @abstractmethod
    async def search(self, query: str) -> list[ScrapedProduct]:
        ...

    async def search_batch(self, queries: list[str]) -> list[ScrapedProduct]:
        all_results = []
        for i, query in enumerate(queries):
            try:
                products = await self.search(query)
                all_results.extend(products)
                self.logger.info("[%d/%d] '%s' -> %d products", i + 1, len(queries), query, len(products))
            except Exception as e:
                self.errors.append(f"{query}: {e}")
                self.logger.error("[%d/%d] '%s' failed: %s", i + 1, len(queries), query, e)
            if i < len(queries) - 1:
                await asyncio.sleep(self.RATE_LIMIT_DELAY)
        self.results = all_results
        return all_results

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        """Only retry server errors and connection failures, not client errors (4xx)."""
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code >= 500
        return isinstance(exc, (httpx.ConnectError, httpx.ReadTimeout))

    async def _get_with_retry(self, client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
        for attempt in range(self.MAX_RETRIES):
            try:
                resp = await client.get(url, **kwargs)
                resp.raise_for_status()
                return resp
            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout) as e:
                if not self._is_retryable(e) or attempt == self.MAX_RETRIES - 1:
                    raise
                wait = 2 ** attempt
                self.logger.warning("Retry %d/%d for %s: %s", attempt + 1, self.MAX_RETRIES, url, e)
                await asyncio.sleep(wait)

    async def _post_with_retry(self, client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
        for attempt in range(self.MAX_RETRIES):
            try:
                resp = await client.post(url, **kwargs)
                resp.raise_for_status()
                return resp
            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout) as e:
                if not self._is_retryable(e) or attempt == self.MAX_RETRIES - 1:
                    raise
                wait = 2 ** attempt
                self.logger.warning("Retry %d/%d: %s", attempt + 1, self.MAX_RETRIES, e)
                await asyncio.sleep(wait)
