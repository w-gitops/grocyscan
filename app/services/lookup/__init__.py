"""Barcode lookup providers and manager."""

from app.services.lookup.base import BaseLookupProvider, LookupResult
from app.services.lookup.manager import LookupManager, lookup_manager
from app.services.lookup.openfoodfacts import OpenFoodFactsProvider

__all__ = [
    "BaseLookupProvider",
    "LookupResult",
    "LookupManager",
    "lookup_manager",
    "OpenFoodFactsProvider",
]
