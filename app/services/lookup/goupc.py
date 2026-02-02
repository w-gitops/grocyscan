"""go-upc.com barcode lookup provider."""

import time
from typing import Any

import httpx

from app.config import settings
from app.core.logging import get_logger
from app.services.lookup.base import BaseLookupProvider, LookupResult

logger = get_logger(__name__)

# go-upc API base URL
GOUPC_API_BASE = "https://go-upc.com/api/v1"


class GoUPCProvider(BaseLookupProvider):
    """go-upc.com barcode lookup provider.

    go-upc provides a comprehensive UPC/EAN database with product information.
    API documentation: https://go-upc.com/api
    """

    name = "goupc"

    def __init__(self) -> None:
        self.enabled = settings.goupc_enabled
        self.api_key = settings.goupc_api_key.get_secret_value()
        self.timeout = settings.lookup_timeout_seconds

    async def lookup(self, barcode: str) -> LookupResult:
        """Look up a barcode on go-upc.

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
                    f"{GOUPC_API_BASE}/code/{barcode}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
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

                if not data.get("product"):
                    return LookupResult(
                        barcode=barcode,
                        found=False,
                        provider=self.name,
                        lookup_time_ms=lookup_time_ms,
                    )

                product = data["product"]
                result = self._parse_product(barcode, product, lookup_time_ms)

                logger.info(
                    "Product found in go-upc",
                    barcode=barcode,
                    name=result.name,
                    lookup_time_ms=lookup_time_ms,
                )

                return result

        except httpx.TimeoutException:
            logger.warning("go-upc lookup timed out", barcode=barcode)
            return LookupResult(
                barcode=barcode,
                found=False,
                provider=self.name,
                lookup_time_ms=int((time.time() - start_time) * 1000),
            )
        except httpx.HTTPError as e:
            logger.error("go-upc lookup failed", barcode=barcode, error=str(e))
            return LookupResult(
                barcode=barcode,
                found=False,
                provider=self.name,
                lookup_time_ms=int((time.time() - start_time) * 1000),
            )

    def _parse_product(
        self, barcode: str, product: dict[str, Any], lookup_time_ms: int
    ) -> LookupResult:
        """Parse go-upc product data into LookupResult."""
        name = product.get("name")
        brand = product.get("brand")

        # Build full name
        if name and brand and brand.lower() not in name.lower():
            full_name = f"{brand} {name}"
        else:
            full_name = name

        return LookupResult(
            barcode=barcode,
            found=True,
            provider=self.name,
            name=full_name,
            brand=brand,
            description=product.get("description"),
            category=product.get("category"),
            image_url=product.get("imageUrl"),
            raw_data=product,
            lookup_time_ms=lookup_time_ms,
        )

    async def health_check(self) -> bool:
        """Check if go-upc API is available."""
        if not self.enabled or not self.api_key:
            return False

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                # Check with a known barcode
                response = await client.get(
                    f"{GOUPC_API_BASE}/code/3017620422003",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return response.status_code in (200, 404)
        except Exception:
            return False
