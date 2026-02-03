"""Rate limiting middleware."""

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware.

    For production, use Redis-based rate limiting.
    """

    def __init__(self, app: Callable, requests_per_minute: int = 100) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute
        # Track requests: {ip: [(timestamp, count), ...]}
        self._requests: dict[str, list[tuple[float, int]]] = defaultdict(list)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        """Check rate limit and process request.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response from handler or 429 if rate limited
        """
        # Skip rate limiting in development
        if settings.is_development:
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Check rate limit
        if self._is_rate_limited(client_ip):
            logger.warning("Rate limit exceeded", client_ip=client_ip)
            return Response(
                content='{"error":"RATE_LIMITED","message":"Too many requests"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"},
            )

        # Record request
        self._record_request(client_ip)

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request.

        Handles X-Forwarded-For header for reverse proxy setups.

        Args:
            request: Incoming request

        Returns:
            str: Client IP address
        """
        # Check for forwarded header
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Fall back to direct client
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited.

        Args:
            client_ip: Client IP address

        Returns:
            bool: True if rate limited
        """
        now = time.time()
        window_start = now - self.window_size

        # Clean old entries
        self._requests[client_ip] = [
            (ts, count) for ts, count in self._requests[client_ip]
            if ts > window_start
        ]

        # Count requests in window
        total_requests = sum(count for _, count in self._requests[client_ip])

        return total_requests >= self.requests_per_minute

    def _record_request(self, client_ip: str) -> None:
        """Record a request from client.

        Args:
            client_ip: Client IP address
        """
        now = time.time()

        # Add to current second bucket
        if self._requests[client_ip] and self._requests[client_ip][-1][0] == int(now):
            # Same second, increment count
            ts, count = self._requests[client_ip][-1]
            self._requests[client_ip][-1] = (ts, count + 1)
        else:
            # New second
            self._requests[client_ip].append((int(now), 1))
