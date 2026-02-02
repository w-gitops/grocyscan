"""Brave Search barcode lookup provider."""

import re
import time
from typing import Any

import httpx

from app.config import settings
from app.core.logging import get_logger
from app.services.lookup.base import BaseLookupProvider, LookupResult

logger = get_logger(__name__)

# Brave Search API base URL
BRAVE_API_BASE = "https://api.search.brave.com/res/v1"


class BraveSearchProvider(BaseLookupProvider):
    """Brave Search barcode lookup provider.

    Uses Brave Search API to find product information when other
    providers fail. Good as a fallback for obscure products.
    """

    name = "brave"

    def __init__(self) -> None:
        self.enabled = settings.brave_enabled
        self.api_key = settings.brave_api_key.get_secret_value()
        self.timeout = settings.lookup_timeout_seconds
        self.use_as_fallback = settings.brave_use_as_fallback

    async def lookup(self, barcode: str) -> LookupResult:
        """Look up a barcode using Brave Search.

        Searches for the barcode and tries to extract product info
        from search results.

        Args:
            barcode: The barcode to look up

        Returns:
            LookupResult: Product information if found
        """
        start_time = time.time()

        if not self.enabled or not self.api_key:
            return LookupResult(
                barcode=barcode,
                found=False,
                provider=self.name,
                lookup_time_ms=0,
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{BRAVE_API_BASE}/web/search",
                    params={
                        "q": f"{barcode} product",
                        "count": 5,
                    },
                    headers={
                        "X-Subscription-Token": self.api_key,
                        "Accept": "application/json",
                    },
                )

                lookup_time_ms = int((time.time() - start_time) * 1000)

                if response.status_code != 200:
                    return LookupResult(
                        barcode=barcode,
                        found=False,
                        provider=self.name,
                        lookup_time_ms=lookup_time_ms,
                    )

                data = response.json()
                web_results = data.get("web", {}).get("results", [])

                if not web_results:
                    return LookupResult(
                        barcode=barcode,
                        found=False,
                        provider=self.name,
                        lookup_time_ms=lookup_time_ms,
                    )

                # Try to extract product info from search results
                result = self._extract_product_info(barcode, web_results, lookup_time_ms)

                if result.found:
                    logger.info(
                        "Product found via Brave Search",
                        barcode=barcode,
                        name=result.name,
                        lookup_time_ms=lookup_time_ms,
                    )

                return result

        except httpx.TimeoutException:
            logger.warning("Brave Search lookup timed out", barcode=barcode)
            return LookupResult(
                barcode=barcode,
                found=False,
                provider=self.name,
                lookup_time_ms=int((time.time() - start_time) * 1000),
            )
        except httpx.HTTPError as e:
            logger.error("Brave Search lookup failed", barcode=barcode, error=str(e))
            return LookupResult(
                barcode=barcode,
                found=False,
                provider=self.name,
                lookup_time_ms=int((time.time() - start_time) * 1000),
            )

    def _extract_product_info(
        self, barcode: str, results: list[dict[str, Any]], lookup_time_ms: int
    ) -> LookupResult:
        """Extract product information from search results.

        Uses heuristics to find product name from search result titles.

        Args:
            barcode: The barcode
            results: Search results
            lookup_time_ms: Lookup duration

        Returns:
            LookupResult: Extracted product info
        """
        # Look for results that seem to be product pages
        product_keywords = ["buy", "product", "amazon", "walmart", "target", "grocery"]

        for result in results:
            title = result.get("title", "")
            description = result.get("description", "")
            url = result.get("url", "")

            # Skip if barcode not in title (likely not relevant)
            if barcode not in title and barcode not in description:
                continue

            # Try to extract product name from title
            # Remove common suffixes like "- Amazon.com", "| Walmart"
            name = re.sub(r"\s*[-|]\s*[A-Za-z]+\.?(com|org|net)?.*$", "", title)
            name = re.sub(rf"\b{barcode}\b", "", name).strip()

            if name and len(name) > 3:
                # Get thumbnail if available
                thumbnail = result.get("thumbnail", {}).get("src")

                return LookupResult(
                    barcode=barcode,
                    found=True,
                    provider=self.name,
                    name=name,
                    description=description[:500] if description else None,
                    image_url=thumbnail,
                    raw_data={"search_results": results[:3]},
                    lookup_time_ms=lookup_time_ms,
                )

        # No good results found
        return LookupResult(
            barcode=barcode,
            found=False,
            provider=self.name,
            lookup_time_ms=lookup_time_ms,
        )

    async def health_check(self) -> bool:
        """Check if Brave Search API is available."""
        if not self.enabled or not self.api_key:
            return False

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{BRAVE_API_BASE}/web/search",
                    params={"q": "test", "count": 1},
                    headers={"X-Subscription-Token": self.api_key},
                )
                return response.status_code == 200
        except Exception:
            return False
