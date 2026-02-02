"""Base class for lookup providers."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class LookupResult(BaseModel):
    """Standard result from a barcode lookup."""

    barcode: str
    found: bool
    provider: str
    name: str | None = None
    brand: str | None = None
    description: str | None = None
    category: str | None = None
    image_url: str | None = None
    quantity: str | None = None
    quantity_unit: str | None = None
    nutrition: dict[str, Any] | None = None
    ingredients: str | None = None
    raw_data: dict[str, Any] | None = None
    lookup_time_ms: int = 0


class BaseLookupProvider(ABC):
    """Abstract base class for lookup providers."""

    name: str = "base"

    def is_enabled(self) -> bool:
        """Check if this provider is enabled in current settings.
        
        Override in subclasses to read from settings service.
        
        Returns:
            bool: True if provider is enabled
        """
        return True

    def get_api_key(self) -> str:
        """Get the API key for this provider from current settings.
        
        Override in subclasses to read from settings service.
        
        Returns:
            str: API key or empty string
        """
        return ""

    @abstractmethod
    async def lookup(self, barcode: str) -> LookupResult:
        """Look up a barcode and return product information.

        Args:
            barcode: The barcode to look up

        Returns:
            LookupResult: The lookup result
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available.

        Returns:
            bool: True if provider is healthy
        """
        pass
