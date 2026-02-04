"""Session management middleware."""

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.core.logging import get_logger
from app.services.auth import get_session

logger = get_logger(__name__)

# Paths that don't require authentication
PUBLIC_PATHS = {
    "/health",
    "/api/health",
    "/api/health/detailed",
    "/api/auth/login",
    "/api/v2/health",
    "/api/v2/auth/login",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/openapi.json",
}


class SessionMiddleware(BaseHTTPMiddleware):
    """Middleware for session-based authentication.

    Validates session cookies and attaches user info to request state.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        """Process request and validate session.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response from handler
        """
        # Skip auth for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Skip auth if disabled
        if not settings.auth_enabled:
            request.state.user_id = "default-user"
            request.state.username = "admin"
            return await call_next(request)

        # API v2 uses Bearer / HOMEBOT-API-KEY; let route dependencies enforce auth
        if request.url.path.startswith("/api/v2/"):
            return await call_next(request)

        # Get session cookie
        session_id = request.cookies.get(settings.session_cookie_name)
        if not session_id:
            # For API requests without session, return 401
            if request.url.path.startswith("/api/"):
                return Response(
                    content='{"error":"AUTHENTICATION_ERROR","message":"Authentication required"}',
                    status_code=401,
                    media_type="application/json",
                )
            # For UI requests, let the handler deal with it
            return await call_next(request)

        # Validate session
        session = get_session(session_id)
        if session is None:
            # Invalid or expired session
            response = await call_next(request)
            # Clear the invalid session cookie
            response.delete_cookie(
                settings.session_cookie_name,
                domain=settings.session_cookie_domain_resolved,
                path="/",
            )
            return response

        # Attach user info to request
        request.state.user_id = session.user_id
        request.state.username = session.username
        request.state.session_id = session.session_id

        return await call_next(request)

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no auth required).

        Args:
            path: Request path

        Returns:
            bool: True if public path
        """
        # Exact match
        if path in PUBLIC_PATHS:
            return True

        # Prefix match for certain paths
        public_prefixes = ("/docs", "/redoc", "/openapi")
        if any(path.startswith(prefix) for prefix in public_prefixes):
            return True

        return False
