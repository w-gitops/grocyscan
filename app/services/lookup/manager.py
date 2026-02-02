"""Lookup manager for orchestrating barcode lookups across providers."""

import asyncio
import time
from typing import Any

from app.core.logging import get_logger
from app.services.cache import cache_service
from app.services.lookup.base import BaseLookupProvider, LookupResult
from app.services.lookup.brave import BraveSearchProvider
from app.services.lookup.goupc import GoUPCProvider
from app.services.lookup.openfoodfacts import OpenFoodFactsProvider
from app.services.lookup.upcitemdb import UPCItemDBProvider

logger = get_logger(__name__)


def _get_lookup_settings():
    """Get current lookup settings from settings service."""
    try:
        from app.services.settings import settings_service
        return settings_service.load().lookup
    except Exception:
        # Fallback to static config if settings service not available
        from app.config import settings
        return settings


class LookupManager:
    """Manages barcode lookups across multiple providers.

    Supports sequential and parallel lookup strategies with Redis caching.
    Settings are read dynamically to support hot-reload.
    """

    def __init__(self) -> None:
        self.providers: dict[str, BaseLookupProvider] = {}
        self.use_cache = True
        self._init_providers()

    def _init_providers(self) -> None:
        """Initialize configured providers based on current settings."""
        lookup_settings = _get_lookup_settings()
        
        # Clear existing providers
        self.providers.clear()
        
        # Create fresh provider instances that read settings dynamically
        available_providers = {
            "openfoodfacts": OpenFoodFactsProvider,
            "goupc": GoUPCProvider,
            "upcitemdb": UPCItemDBProvider,
            "brave": BraveSearchProvider,
        }

        # Get provider order from settings
        provider_order = getattr(lookup_settings, 'provider_order', None)
        if provider_order is None:
            # Fallback to config
            from app.config import settings
            provider_order = settings.provider_list

        # Only include enabled providers in configured order
        for provider_name in provider_order:
            if provider_name in available_providers:
                provider = available_providers[provider_name]()
                if provider.is_enabled():
                    self.providers[provider_name] = provider
                    logger.info(f"Registered lookup provider: {provider_name}")

    def reload(self) -> None:
        """Reload providers with current settings. Call after settings change."""
        logger.info("Reloading lookup providers")
        self._init_providers()
        logger.info(f"Lookup providers reloaded: {list(self.providers.keys())}")

    async def lookup(self, barcode: str, skip_cache: bool = False) -> LookupResult:
        """Look up a barcode using configured strategy.

        Checks cache first, then queries providers if not cached.

        Args:
            barcode: The barcode to look up
            skip_cache: If True, skip cache and query providers directly

        Returns:
            LookupResult: Best result from providers
        """
        # Check cache first
        if self.use_cache and not skip_cache:
            cached = await cache_service.get_lookup_result(barcode)
            if cached:
                logger.info(
                    "Cache hit",
                    barcode=barcode,
                    provider=cached.provider,
                )
                return cached

        # Query providers
        lookup_settings = _get_lookup_settings()
        strategy = getattr(lookup_settings, 'strategy', 'sequential')
        if strategy == "parallel":
            result = await self._lookup_parallel(barcode)
        else:
            result = await self._lookup_sequential(barcode)

        # Cache the result
        if self.use_cache and result.found:
            await cache_service.set_lookup_result(barcode, result)

        return result

    async def _lookup_sequential(self, barcode: str) -> LookupResult:
        """Look up barcode sequentially through providers.

        Stops at the first provider that finds the product.

        Args:
            barcode: The barcode to look up

        Returns:
            LookupResult: First successful result or not found
        """
        start_time = time.time()

        for name, provider in self.providers.items():
            logger.debug(f"Trying provider: {name}", barcode=barcode)
            result = await provider.lookup(barcode)

            if result.found:
                logger.info(
                    "Barcode found",
                    barcode=barcode,
                    provider=name,
                    total_time_ms=int((time.time() - start_time) * 1000),
                )
                return result

        # Not found in any provider
        total_time_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "Barcode not found in any provider",
            barcode=barcode,
            providers_tried=list(self.providers.keys()),
            total_time_ms=total_time_ms,
        )

        return LookupResult(
            barcode=barcode,
            found=False,
            provider="none",
            lookup_time_ms=total_time_ms,
        )

    async def _lookup_parallel(self, barcode: str) -> LookupResult:
        """Look up barcode in parallel across all providers.

        Returns the best result based on data quality.

        Args:
            barcode: The barcode to look up

        Returns:
            LookupResult: Best result from all providers
        """
        start_time = time.time()

        # Create tasks for all providers
        tasks = [provider.lookup(barcode) for provider in self.providers.values()]

        # Wait for all results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        valid_results: list[LookupResult] = []
        for result in results:
            if isinstance(result, LookupResult) and result.found:
                valid_results.append(result)

        total_time_ms = int((time.time() - start_time) * 1000)

        if not valid_results:
            logger.info(
                "Barcode not found in any provider (parallel)",
                barcode=barcode,
                providers_tried=list(self.providers.keys()),
                total_time_ms=total_time_ms,
            )
            return LookupResult(
                barcode=barcode,
                found=False,
                provider="none",
                lookup_time_ms=total_time_ms,
            )

        # Select best result (most complete data)
        best_result = self._select_best_result(valid_results)
        best_result.lookup_time_ms = total_time_ms

        logger.info(
            "Barcode found (parallel)",
            barcode=barcode,
            provider=best_result.provider,
            candidates=len(valid_results),
            total_time_ms=total_time_ms,
        )

        return best_result

    def _select_best_result(self, results: list[LookupResult]) -> LookupResult:
        """Select the best result from multiple lookup results.

        Scores results based on data completeness.

        Args:
            results: List of successful lookup results

        Returns:
            LookupResult: The best result
        """
        if len(results) == 1:
            return results[0]

        def score_result(result: LookupResult) -> int:
            """Calculate quality score for a result."""
            score = 0
            if result.name:
                score += 10
            if result.brand:
                score += 5
            if result.description:
                score += 3
            if result.category:
                score += 5
            if result.image_url:
                score += 8
            if result.nutrition:
                score += 7
            if result.ingredients:
                score += 3
            return score

        # Sort by score (highest first) and return best
        results.sort(key=score_result, reverse=True)
        return results[0]

    async def health_check(self) -> dict[str, bool]:
        """Check health of all providers.

        Returns:
            dict: Provider name -> health status
        """
        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = await provider.health_check()
            except Exception:
                results[name] = False
        return results

    def get_provider_status(self) -> dict[str, Any]:
        """Get status of all providers.

        Returns:
            dict: Provider status information
        """
        lookup_settings = _get_lookup_settings()
        return {
            "strategy": getattr(lookup_settings, 'strategy', 'sequential'),
            "providers": [
                {
                    "name": name,
                    "enabled": provider.is_enabled(),
                    "order": i,
                }
                for i, (name, provider) in enumerate(self.providers.items())
            ],
        }


# Global lookup manager instance
lookup_manager = LookupManager()
