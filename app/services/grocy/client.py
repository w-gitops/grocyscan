"""Grocy API client for inventory management."""

from typing import Any

import httpx

from app.config import settings
from app.core.exceptions import GrocyError
from app.core.logging import get_logger

logger = get_logger(__name__)


def _get_grocy_settings() -> tuple[str, str, int]:
    """Get Grocy settings, preferring settings_service over environment.
    
    Returns:
        Tuple of (api_url, api_key, timeout)
    """
    try:
        from app.services.settings import settings_service
        grocy = settings_service.get_section("grocy")
        api_url = grocy.api_url or settings.grocy_api_url
        api_key = grocy.api_key or settings.grocy_api_key.get_secret_value()
        timeout = settings.grocy_timeout_seconds
        return api_url.rstrip("/"), api_key, timeout
    except Exception:
        # Fallback to environment settings
        return (
            settings.grocy_api_url.rstrip("/"),
            settings.grocy_api_key.get_secret_value(),
            settings.grocy_timeout_seconds,
        )


class GrocyClient:
    """Client for the Grocy REST API.

    Handles authentication and provides methods for common operations.
    API documentation: https://demo.grocy.info/api
    """

    def __init__(self) -> None:
        # Settings are read dynamically in each request via properties
        pass

    @property
    def api_url(self) -> str:
        """Get API URL dynamically from settings."""
        api_url, _, _ = _get_grocy_settings()
        return api_url

    @property
    def api_key(self) -> str:
        """Get API key dynamically from settings."""
        _, api_key, _ = _get_grocy_settings()
        return api_key

    @property
    def timeout(self) -> int:
        """Get timeout dynamically from settings."""
        _, _, timeout = _get_grocy_settings()
        return timeout

    @property
    def headers(self) -> dict[str, str]:
        """Get request headers with API key."""
        return {
            "GROCY-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any] | list[Any] | None:
        """Make an authenticated request to Grocy API.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            **kwargs: Additional arguments for httpx

        Returns:
            Response JSON data

        Raises:
            GrocyError: If request fails
        """
        url = f"{self.api_url}/api{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    **kwargs,
                )

                if response.status_code == 204:
                    return None

                if response.status_code >= 400:
                    error_msg = response.text
                    logger.error(
                        "Grocy API error",
                        status_code=response.status_code,
                        error=error_msg,
                        endpoint=endpoint,
                    )
                    raise GrocyError(
                        f"Grocy API error: {response.status_code}",
                        details={"status_code": response.status_code, "error": error_msg},
                    )

                return response.json()

        except httpx.TimeoutException:
            logger.error("Grocy API timeout", endpoint=endpoint)
            raise GrocyError("Grocy API request timed out")
        except httpx.HTTPError as e:
            logger.error("Grocy API HTTP error", endpoint=endpoint, error=str(e))
            raise GrocyError(f"Grocy API error: {e}")

    # ==================== System ====================

    async def health_check(self) -> bool:
        """Check if Grocy API is reachable.

        Returns:
            bool: True if API is healthy
        """
        try:
            await self._request("GET", "/system/info")
            return True
        except Exception:
            return False

    async def get_system_info(self) -> dict[str, Any]:
        """Get Grocy system information.

        Returns:
            dict: System info including version
        """
        result = await self._request("GET", "/system/info")
        return result or {}

    # ==================== Products ====================

    async def get_products(self) -> list[dict[str, Any]]:
        """Get all products.

        Returns:
            list: All products
        """
        result = await self._request("GET", "/objects/products")
        return result if isinstance(result, list) else []

    async def get_product(self, product_id: int) -> dict[str, Any] | None:
        """Get a product by ID.

        Args:
            product_id: Grocy product ID

        Returns:
            dict: Product data or None if not found
        """
        try:
            result = await self._request("GET", f"/objects/products/{product_id}")
            return result if isinstance(result, dict) else None
        except GrocyError:
            return None

    async def get_product_by_barcode(self, barcode: str) -> dict[str, Any] | None:
        """Get a product by barcode.

        Args:
            barcode: Product barcode

        Returns:
            dict: Product data or None if not found
        """
        try:
            result = await self._request("GET", f"/stock/products/by-barcode/{barcode}")
            return result.get("product") if isinstance(result, dict) else None
        except GrocyError:
            return None

    async def create_product(
        self,
        name: str,
        description: str | None = None,
        location_id: int | None = None,
        quantity_unit_id: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create a new product.

        Args:
            name: Product name
            description: Product description
            location_id: Default location ID
            quantity_unit_id: Quantity unit ID
            **kwargs: Additional product fields

        Returns:
            dict: Created product data
        """
        # Minimal required fields for Grocy 4.x
        data = {
            "name": name,
            "description": description or "",
            "location_id": location_id or 1,
            "qu_id_purchase": quantity_unit_id or 1,
            "qu_id_stock": quantity_unit_id or 1,
            **kwargs,
        }

        result = await self._request("POST", "/objects/products", json=data)
        logger.info("Product created in Grocy", name=name)
        return result if isinstance(result, dict) else {"id": 0}

    async def update_product(
        self, product_id: int, **kwargs: Any
    ) -> dict[str, Any] | None:
        """Update a product.

        Args:
            product_id: Grocy product ID
            **kwargs: Fields to update

        Returns:
            dict: Updated product data
        """
        result = await self._request(
            "PUT", f"/objects/products/{product_id}", json=kwargs
        )
        logger.info("Product updated in Grocy", product_id=product_id)
        return result if isinstance(result, dict) else None

    async def add_barcode_to_product(
        self, product_id: int, barcode: str
    ) -> dict[str, Any]:
        """Add a barcode to a product.

        Args:
            product_id: Grocy product ID
            barcode: Barcode to add

        Returns:
            dict: Created barcode record
        """
        data = {
            "product_id": product_id,
            "barcode": barcode,
        }
        result = await self._request("POST", "/objects/product_barcodes", json=data)
        logger.info("Barcode added to product", product_id=product_id, barcode=barcode)
        return result if isinstance(result, dict) else {}

    # ==================== Stock ====================

    async def add_to_stock(
        self,
        product_id: int,
        amount: float = 1,
        best_before_date: str | None = None,
        price: float | None = None,
        location_id: int | None = None,
    ) -> dict[str, Any]:
        """Add stock for a product.

        Args:
            product_id: Grocy product ID
            amount: Quantity to add
            best_before_date: Best before date (YYYY-MM-DD)
            price: Price per unit
            location_id: Storage location ID

        Returns:
            dict: Stock transaction info
        """
        data: dict[str, Any] = {
            "amount": amount,
            "transaction_type": "purchase",
        }

        if best_before_date:
            data["best_before_date"] = best_before_date
        if price is not None:
            data["price"] = price
        if location_id:
            data["location_id"] = location_id

        result = await self._request(
            "POST", f"/stock/products/{product_id}/add", json=data
        )
        logger.info(
            "Stock added",
            product_id=product_id,
            amount=amount,
            best_before=best_before_date,
        )
        return result if isinstance(result, dict) else {}

    async def consume_stock(
        self,
        product_id: int,
        amount: float = 1,
        spoiled: bool = False,
    ) -> dict[str, Any]:
        """Consume stock for a product.

        Args:
            product_id: Grocy product ID
            amount: Quantity to consume
            spoiled: Whether the stock was spoiled

        Returns:
            dict: Stock transaction info
        """
        data = {
            "amount": amount,
            "transaction_type": "consume",
            "spoiled": spoiled,
        }

        result = await self._request(
            "POST", f"/stock/products/{product_id}/consume", json=data
        )
        logger.info("Stock consumed", product_id=product_id, amount=amount)
        return result if isinstance(result, dict) else {}

    async def get_stock(self) -> list[dict[str, Any]]:
        """Get current stock overview.

        Returns:
            list: All stock entries
        """
        result = await self._request("GET", "/stock")
        return result if isinstance(result, list) else []

    async def get_product_stock(self, product_id: int) -> dict[str, Any] | None:
        """Get stock for a specific product.

        Args:
            product_id: Grocy product ID

        Returns:
            dict: Stock information for product
        """
        result = await self._request("GET", f"/stock/products/{product_id}")
        return result if isinstance(result, dict) else None

    # ==================== Locations ====================

    async def get_locations(self) -> list[dict[str, Any]]:
        """Get all locations.

        Returns:
            list: All locations
        """
        result = await self._request("GET", "/objects/locations")
        return result if isinstance(result, list) else []

    async def get_location(self, location_id: int) -> dict[str, Any] | None:
        """Get a location by ID.

        Args:
            location_id: Grocy location ID

        Returns:
            dict: Location data or None if not found
        """
        try:
            result = await self._request("GET", f"/objects/locations/{location_id}")
            return result if isinstance(result, dict) else None
        except GrocyError:
            return None

    async def create_location(
        self,
        name: str,
        description: str | None = None,
        is_freezer: bool = False,
    ) -> dict[str, Any]:
        """Create a new location.

        Args:
            name: Location name
            description: Location description
            is_freezer: Whether this is a freezer location

        Returns:
            dict: Created location data
        """
        data = {
            "name": name,
            "description": description or "",
            "is_freezer": int(is_freezer),
        }

        result = await self._request("POST", "/objects/locations", json=data)
        logger.info("Location created in Grocy", name=name)
        return result if isinstance(result, dict) else {}

    # ==================== Quantity Units ====================

    async def get_quantity_units(self) -> list[dict[str, Any]]:
        """Get all quantity units.

        Returns:
            list: All quantity units
        """
        result = await self._request("GET", "/objects/quantity_units")
        return result if isinstance(result, list) else []


# Global client instance
grocy_client = GrocyClient()
