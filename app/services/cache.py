"""Redis caching service for barcode lookups."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import redis.asyncio as redis

from app.config import settings
from app.core.logging import get_logger
from app.services.lookup.base import LookupResult

logger = get_logger(__name__)


class CacheService:
    """Redis-based caching service for barcode lookups.

    Provides a simple interface for caching lookup results with TTL.
    """

    def __init__(self) -> None:
        self._redis: redis.Redis | None = None
        self._connected = False

    async def connect(self) -> None:
        """Connect to Redis server."""
        try:
            self._redis = redis.from_url(
                settings.redis_url,
                password=settings.redis_password.get_secret_value() or None,
                decode_responses=True,
            )
            # Test connection
            await self._redis.ping()
            self._connected = True
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.warning("Failed to connect to Redis", error=str(e))
            self._connected = False

    async def disconnect(self) -> None:
        """Disconnect from Redis server."""
        if self._redis:
            await self._redis.close()
            self._connected = False

    async def get_lookup_result(self, barcode: str) -> LookupResult | None:
        """Get cached lookup result for a barcode.

        Args:
            barcode: The barcode to look up

        Returns:
            LookupResult if found in cache, None otherwise
        """
        if not self._connected or not self._redis:
            return None

        try:
            key = f"lookup:{barcode}"
            data = await self._redis.get(key)

            if data:
                parsed = json.loads(data)
                logger.debug("Cache hit", barcode=barcode, provider=parsed.get("provider"))
                return LookupResult(**parsed)

            logger.debug("Cache miss", barcode=barcode)
            return None

        except Exception as e:
            logger.warning("Cache get failed", barcode=barcode, error=str(e))
            return None

    async def set_lookup_result(
        self,
        barcode: str,
        result: LookupResult,
        ttl_days: int | None = None,
    ) -> bool:
        """Cache a lookup result.

        Args:
            barcode: The barcode
            result: The lookup result to cache
            ttl_days: Time to live in days (defaults to settings.cache_ttl_days)

        Returns:
            bool: True if cached successfully
        """
        if not self._connected or not self._redis:
            return False

        try:
            key = f"lookup:{barcode}"
            ttl = ttl_days or settings.cache_ttl_days
            ttl_seconds = ttl * 24 * 60 * 60

            # Serialize result
            data = result.model_dump_json()

            await self._redis.setex(key, ttl_seconds, data)
            logger.debug(
                "Cached lookup result",
                barcode=barcode,
                provider=result.provider,
                ttl_days=ttl,
            )
            return True

        except Exception as e:
            logger.warning("Cache set failed", barcode=barcode, error=str(e))
            return False

    async def invalidate(self, barcode: str) -> bool:
        """Invalidate cached result for a barcode.

        Args:
            barcode: The barcode to invalidate

        Returns:
            bool: True if invalidated
        """
        if not self._connected or not self._redis:
            return False

        try:
            key = f"lookup:{barcode}"
            await self._redis.delete(key)
            logger.debug("Cache invalidated", barcode=barcode)
            return True

        except Exception as e:
            logger.warning("Cache invalidate failed", barcode=barcode, error=str(e))
            return False

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            dict: Cache statistics
        """
        if not self._connected or not self._redis:
            return {"connected": False}

        try:
            info = await self._redis.info("stats")
            keys = await self._redis.dbsize()

            return {
                "connected": True,
                "total_keys": keys,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0)
                    / max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0))
                ),
            }

        except Exception as e:
            logger.warning("Failed to get cache stats", error=str(e))
            return {"connected": False, "error": str(e)}

    async def health_check(self) -> bool:
        """Check if Redis is available.

        Returns:
            bool: True if Redis is healthy
        """
        if not self._redis:
            return False

        try:
            await self._redis.ping()
            return True
        except Exception:
            return False


# Global cache service instance
cache_service = CacheService()
