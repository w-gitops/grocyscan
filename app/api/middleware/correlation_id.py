"""Correlation ID middleware: set and log request correlation ID (Phase 1)."""

import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

HEADER_REQUEST_ID = "X-Request-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Set correlation ID per request and bind to structlog context."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        correlation_id = request.headers.get(HEADER_REQUEST_ID) or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        try:
            response = await call_next(request)
            response.headers[HEADER_REQUEST_ID] = correlation_id
            return response
        finally:
            structlog.contextvars.unbind_contextvars("correlation_id")
