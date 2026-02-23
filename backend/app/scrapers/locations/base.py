import asyncio
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod

import httpx


@dataclass
class ScrapedLocation:
    chain: str
    branch_code: str
    name: str
    address: str = ""
    comuna: str = ""
    lat: float = 0.0
    lng: float = 0.0
    phone: str = ""
    hours: str = ""


class BaseLocationScraper(ABC):
    CHAIN: str = ""
    RATE_LIMIT_DELAY: float = 1.0
    MAX_RETRIES: int = 3

    def __init__(self):
        self.logger = logging.getLogger(f"scraper.locations.{self.CHAIN}")
        self.results: list[ScrapedLocation] = []
        self.errors: list[str] = []

    @abstractmethod
    async def scrape_locations(self) -> list[ScrapedLocation]:
        ...

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
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

    def _safe_json(self, response: httpx.Response) -> dict | list | None:
        try:
            return response.json()
        except Exception as e:
            self.logger.error("JSON decode error for %s: %s", response.url, e)
            return None
