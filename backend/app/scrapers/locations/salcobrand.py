import asyncio
import re

import httpx
from bs4 import BeautifulSoup

from app.scrapers.locations.base import BaseLocationScraper, ScrapedLocation


class SalcobrandLocationScraper(BaseLocationScraper):
    CHAIN = "salcobrand"
    BASE_URL = "https://salcobrand.cl/content/servicios/mapa"
    MAX_PAGES = 60
    RATE_LIMIT_DELAY = 2.0

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-CL,es;q=0.9,en;q=0.5",
    }

    # Regex to extract lat/lng from Google Maps direction links
    # Matches patterns like maps/dir/-33.4489,-70.6693 or @-33.4489,-70.6693
    COORDS_RE = re.compile(r"(?:maps/dir/|@)(-?\d+\.\d+),\s*(-?\d+\.\d+)")

    async def scrape_locations(self) -> list[ScrapedLocation]:
        seen: set[tuple[str, str]] = set()  # (name, comuna) for dedup
        seen_coords: set[tuple[float, float]] = set()
        results: list[ScrapedLocation] = []
        store_index = 0

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
        ) as client:
            for page in range(1, self.MAX_PAGES + 1):
                try:
                    url = f"{self.BASE_URL}?page={page}"
                    resp = await self._get_with_retry(
                        client,
                        url,
                        headers=self.HEADERS,
                    )
                    html = resp.text
                    stores_on_page = self._parse_page(html, store_index, seen, seen_coords)

                    if not stores_on_page:
                        self.logger.info(
                            "No stores found on page %d, stopping pagination", page
                        )
                        break

                    results.extend(stores_on_page)
                    store_index += len(stores_on_page)
                    self.logger.info(
                        "Page %d: found %d stores (total: %d)",
                        page,
                        len(stores_on_page),
                        len(results),
                    )

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        self.logger.info(
                            "Page %d returned 404, stopping pagination", page
                        )
                        break
                    self.errors.append(f"Salcobrand page {page}: HTTP {e.response.status_code}")
                    self.logger.error("HTTP error on page %d: %s", page, e)
                except Exception as e:
                    self.errors.append(f"Salcobrand page {page}: {e}")
                    self.logger.error("Error fetching page %d: %s", page, e)

                await asyncio.sleep(self.RATE_LIMIT_DELAY)

        self.logger.info(
            "Salcobrand scraping complete: %d locations, %d errors",
            len(results),
            len(self.errors),
        )
        self.results = results
        return results

    def _parse_page(
        self,
        html: str,
        start_index: int,
        seen: set[tuple[str, str]],
        seen_coords: set[tuple[float, float]],
    ) -> list[ScrapedLocation]:
        soup = BeautifulSoup(html, "html.parser")
        pills = soup.find_all("li", class_=lambda c: c and "stores__pill" in c)

        if not pills:
            return []

        locations: list[ScrapedLocation] = []

        for pill in pills:
            try:
                location = self._parse_store_pill(pill)
                if not location:
                    continue

                # Dedup by (address, comuna)
                dedup_key = (location.address.lower().strip(), location.comuna.lower().strip())
                if dedup_key in seen:
                    self.logger.debug("Duplicate store skipped: %s, %s", location.address, location.comuna)
                    continue

                # Dedup by coordinates (if we have valid ones)
                if location.lat != 0.0 and location.lng != 0.0:
                    coord_key = (round(location.lat, 5), round(location.lng, 5))
                    if coord_key in seen_coords:
                        self.logger.debug(
                            "Duplicate coords skipped: %s at (%s, %s)",
                            location.name, location.lat, location.lng,
                        )
                        continue
                    seen_coords.add(coord_key)

                seen.add(dedup_key)

                # Assign branch code from index
                location.branch_code = f"sb_{start_index + len(locations):04d}"

                locations.append(location)

            except Exception as e:
                self.logger.warning("Skipping malformed Salcobrand store pill: %s", e)

        return locations

    def _parse_store_pill(self, pill) -> ScrapedLocation | None:
        """Extract store data from a single li.stores__pill element."""

        # Extract address
        address = self._extract_text_by_class(pill, "stores__content--is-address")

        # Extract comuna
        comuna = self._extract_text_by_class(pill, "stores__content--is-county")

        # Extract schedule (hours)
        hours = self._extract_text_by_class(pill, "stores__content--is-schedule")

        # Extract lat/lng from Google Maps link
        lat, lng = self._extract_coords(pill)

        # Skip if no address
        if not address:
            return None

        # Name = "Salcobrand {comuna}" since stores don't have individual names
        name = f"Salcobrand {comuna}" if comuna else "Salcobrand"

        return ScrapedLocation(
            chain=self.CHAIN,
            branch_code="",  # assigned later by index
            name=name,
            address=address,
            comuna=comuna,
            lat=lat,
            lng=lng,
            phone="",
            hours=hours,
        )

    def _extract_text_by_class(
        self,
        element,
        class_name: str,
        exclude: list[str] | None = None,
    ) -> str:
        """
        Find a div whose class contains class_name and return its nested <p> text.

        If `exclude` is provided, find divs matching class_name but NOT matching
        any class in exclude -- used to get the store name from the generic
        stores__content div that is not address/county/region.
        """
        if exclude:
            # Find all divs with the target class, then filter out excluded classes
            candidates = element.find_all(
                "div",
                class_=lambda c: c and class_name in c,
            )
            for candidate in candidates:
                classes = candidate.get("class", [])
                class_str = " ".join(classes)
                if not any(ex in class_str for ex in exclude):
                    # Get text from <p> inside, or fallback to div text
                    p_tag = candidate.find("p")
                    if p_tag:
                        return p_tag.get_text(strip=True)
                    text = candidate.get_text(strip=True)
                    if text:
                        return text
            return ""

        div = element.find(
            "div",
            class_=lambda c: c and class_name in c,
        )
        if not div:
            return ""

        p_tag = div.find("p")
        if p_tag:
            return p_tag.get_text(strip=True)
        return div.get_text(strip=True)

    def _extract_coords(self, element) -> tuple[float, float]:
        """Extract latitude and longitude from a Google Maps link in the element."""
        # Look for any anchor tag with a Google Maps URL
        links = element.find_all("a", href=True)
        for link in links:
            href = link["href"]
            if "google.com/maps" in href or "maps.google" in href:
                match = self.COORDS_RE.search(href)
                if match:
                    try:
                        lat = float(match.group(1))
                        lng = float(match.group(2))
                        # Sanity check: Chile coords roughly between -17 and -56 lat, -66 and -76 lng
                        if -60 <= lat <= -15 and -80 <= lng <= -60:
                            return lat, lng
                        self.logger.debug(
                            "Coords out of Chile range: (%s, %s)", lat, lng
                        )
                    except (ValueError, IndexError):
                        pass

        return 0.0, 0.0

