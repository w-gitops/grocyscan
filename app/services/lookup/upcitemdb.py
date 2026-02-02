"""UPCitemdb barcode lookup provider."""

import time
from typing import Any

import httpx

from app.core.logging import get_logger
from app.services.lookup.base import BaseLookupProvider, LookupResult

logger = get_logger(__name__)

# UPCitemdb API base URL
UPCITEMDB_API_BASE = "https://api.upcitemdb.com/prod/trial"


def _get_settings():
    """Get current lookup settings."""
    try:
        from app.services.settings import settings_service
        return settings_service.load().lookup
    except Exception:
        from app.config import settings
        return settings


class UPCItemDBProvider(BaseLookupProvider):
    """UPCitemdb barcode lookup provider.

    UPCitemdb provides UPC/EAN product lookup.
    API documentation: https://www.upcitemdb.com/api/explorer
    """

    name = "upcitemdb"

    def __init__(self) -> None:
        pass  # Settings read dynamically

    def is_enabled(self) -> bool:
        """Check if UPCitemdb is enabled."""
        return _get_settings().upcitemdb_enabled

    def get_api_key(self) -> str:
        """Get UPCitemdb API key."""
        s = _get_settings()
        if hasattr(s, 'upcitemdb_api_key'):
            key = s.upcitemdb_api_key
            return key.get_secret_value() if hasattr(key, 'get_secret_value') else key
        return ""

    @property
    def timeout(self) -> int:
        """Get lookup timeout."""
        return _get_settings().timeout_seconds

    async def lookup(self, barcode: str) -> LookupResult:
        """Look up a barcode on UPCitemdb.

        Args:
            barcode: The barcode to look up

        Returns:
            LookupResult: Product information if found
        """
        start_time = time.time()

        if not self.is_enabled():
            return LookupResult(
                barcode=barcode,
                found=False,
                provider=self.name,
                lookup_time_ms=0,
            )

        try:
            headers = {"Content-Type": "application/json"}
            api_key = self.get_api_key()
            if api_key:
                headers["user_key"] = api_key

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{UPCITEMDB_API_BASE}/lookup",
                    params={"upc": barcode},
                    headers=headers,
                )

                lookup_time_ms = int((time.time() - start_time) * 1000)

                if response.status_code == 404:
                    return LookupResult(
                        barcode=barcode,
                        found=False,
                        provider=self.name,
                        lookup_time_ms=lookup_time_ms,
                    )

                response.raise_for_status()
                data = response.json()

                items = data.get("items", [])
                if not items:
                    return LookupResult(
                        barcode=barcode,
                        found=False,
                        provider=self.name,
                        lookup_time_ms=lookup_time_ms,
                    )

                # Use first item
                product = items[0]
                result = self._parse_product(barcode, product, lookup_time_ms)

                logger.info(
                    "Product found in UPCitemdb",
                    barcode=barcode,
                    name=result.name,
                    lookup_time_ms=lookup_time_ms,
                )

                return result

        except httpx.TimeoutException:
            logger.warning("UPCitemdb lookup timed out", barcode=barcode)
            return LookupResult(
                barcode=barcode,
                found=False,
                provider=self.name,
                lookup_time_ms=int((time.time() - start_time) * 1000),
            )
        except httpx.HTTPError as e:
            logger.error("UPCitemdb lookup failed", barcode=barcode, error=str(e))
            return LookupResult(
                barcode=barcode,
                found=False,
                provider=self.name,
                lookup_time_ms=int((time.time() - start_time) * 1000),
            )

    def _parse_product(
        self, barcode: str, product: dict[str, Any], lookup_time_ms: int
    ) -> LookupResult:
        """Parse UPCitemdb product data into LookupResult."""
        title = product.get("title")
        brand = product.get("brand")

        # Get first image if available
        images = product.get("images", [])
        image_url = images[0] if images else None

        # Get category
        category = product.get("category")

        return LookupResult(
            barcode=barcode,
            found=True,
            provider=self.name,
            name=title,
            brand=brand,
            description=product.get("description"),
            category=category,
            image_url=image_url,
            raw_data=product,
            lookup_time_ms=lookup_time_ms,
        )

    async def health_check(self) -> bool:
        """Check if UPCitemdb API is available."""
        if not self.is_enabled():
            return False

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{UPCITEMDB_API_BASE}/lookup",
                    params={"upc": "3017620422003"},
                )
                return response.status_code in (200, 404)
        except Exception:
            return False
