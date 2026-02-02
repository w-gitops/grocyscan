"""OpenFoodFacts barcode lookup provider."""

import time
from typing import Any

import httpx

from app.config import settings
from app.core.logging import get_logger
from app.services.lookup.base import BaseLookupProvider, LookupResult

logger = get_logger(__name__)

# OpenFoodFacts API base URL
OFF_API_BASE = "https://world.openfoodfacts.org/api/v2"


class OpenFoodFactsProvider(BaseLookupProvider):
    """OpenFoodFacts barcode lookup provider.

    OpenFoodFacts is a free, open, collaborative database of food products.
    API documentation: https://wiki.openfoodfacts.org/API
    """

    name = "openfoodfacts"

    def __init__(self) -> None:
        self.enabled = settings.openfoodfacts_enabled
        self.user_agent = settings.openfoodfacts_user_agent
        self.timeout = settings.lookup_timeout_seconds

    async def lookup(self, barcode: str) -> LookupResult:
        """Look up a barcode on OpenFoodFacts.

        Args:
            barcode: The barcode to look up (EAN-13, UPC-A, etc.)

        Returns:
            LookupResult: Product information if found
        """
        start_time = time.time()

        if not self.enabled:
            return LookupResult(
                barcode=barcode,
                found=False,
                provider=self.name,
                lookup_time_ms=0,
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{OFF_API_BASE}/product/{barcode}",
                    headers={"User-Agent": self.user_agent},
                    params={
                        "fields": "code,product_name,brands,generic_name,categories,"
                        "image_url,quantity,nutrition_grades,nutriments,"
                        "ingredients_text,labels"
                    },
                )

                lookup_time_ms = int((time.time() - start_time) * 1000)

                if response.status_code == 404:
                    logger.debug("Product not found in OpenFoodFacts", barcode=barcode)
                    return LookupResult(
                        barcode=barcode,
                        found=False,
                        provider=self.name,
                        lookup_time_ms=lookup_time_ms,
                    )

                response.raise_for_status()
                data = response.json()

                if data.get("status") != 1:
                    logger.debug(
                        "Product not found in OpenFoodFacts",
                        barcode=barcode,
                        status=data.get("status"),
                    )
                    return LookupResult(
                        barcode=barcode,
                        found=False,
                        provider=self.name,
                        lookup_time_ms=lookup_time_ms,
                    )

                product = data.get("product", {})
                result = self._parse_product(barcode, product, lookup_time_ms)

                logger.info(
                    "Product found in OpenFoodFacts",
                    barcode=barcode,
                    name=result.name,
                    lookup_time_ms=lookup_time_ms,
                )

                return result

        except httpx.TimeoutException:
            logger.warning("OpenFoodFacts lookup timed out", barcode=barcode)
            return LookupResult(
                barcode=barcode,
                found=False,
                provider=self.name,
                lookup_time_ms=int((time.time() - start_time) * 1000),
            )
        except httpx.HTTPError as e:
            logger.error("OpenFoodFacts lookup failed", barcode=barcode, error=str(e))
            return LookupResult(
                barcode=barcode,
                found=False,
                provider=self.name,
                lookup_time_ms=int((time.time() - start_time) * 1000),
            )

    def _parse_product(
        self, barcode: str, product: dict[str, Any], lookup_time_ms: int
    ) -> LookupResult:
        """Parse OpenFoodFacts product data into LookupResult.

        Args:
            barcode: The barcode
            product: Raw product data from API
            lookup_time_ms: Lookup duration

        Returns:
            LookupResult: Parsed product information
        """
        # Extract name (prefer product_name, fall back to generic_name)
        name = product.get("product_name") or product.get("generic_name")

        # Extract brand
        brand = product.get("brands")
        if brand and "," in brand:
            brand = brand.split(",")[0].strip()

        # Build full name with brand if available
        if name and brand and brand.lower() not in name.lower():
            full_name = f"{brand} {name}"
        else:
            full_name = name

        # Extract category (first category from comma-separated list)
        categories = product.get("categories", "")
        category = None
        if categories:
            # Categories are comma-separated, take the most specific (last)
            category_list = [c.strip() for c in categories.split(",")]
            if category_list:
                category = category_list[-1]

        # Extract quantity and unit
        quantity_str = product.get("quantity", "")
        quantity = None
        quantity_unit = None
        if quantity_str:
            # Try to parse quantity like "500g" or "1L"
            import re

            match = re.match(r"([\d.]+)\s*(\w+)", quantity_str)
            if match:
                quantity = match.group(1)
                quantity_unit = match.group(2).lower()

        # Extract nutrition data
        nutriments = product.get("nutriments", {})
        nutrition = None
        if nutriments:
            nutrition = {
                "energy_kcal": nutriments.get("energy-kcal_100g"),
                "fat": nutriments.get("fat_100g"),
                "saturated_fat": nutriments.get("saturated-fat_100g"),
                "carbohydrates": nutriments.get("carbohydrates_100g"),
                "sugars": nutriments.get("sugars_100g"),
                "fiber": nutriments.get("fiber_100g"),
                "proteins": nutriments.get("proteins_100g"),
                "salt": nutriments.get("salt_100g"),
                "nutrition_grade": product.get("nutrition_grades"),
            }
            # Remove None values
            nutrition = {k: v for k, v in nutrition.items() if v is not None}

        return LookupResult(
            barcode=barcode,
            found=True,
            provider=self.name,
            name=full_name,
            brand=brand,
            description=product.get("generic_name"),
            category=category,
            image_url=product.get("image_url"),
            quantity=quantity,
            quantity_unit=quantity_unit,
            nutrition=nutrition if nutrition else None,
            ingredients=product.get("ingredients_text"),
            raw_data=product,
            lookup_time_ms=lookup_time_ms,
        )

    async def health_check(self) -> bool:
        """Check if OpenFoodFacts API is available.

        Returns:
            bool: True if API is reachable
        """
        if not self.enabled:
            return False

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{OFF_API_BASE}/product/3017620422003",  # Nutella
                    headers={"User-Agent": self.user_agent},
                )
                return response.status_code == 200
        except Exception:
            return False
