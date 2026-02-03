"""API v2 dependencies: JWT and API key auth (Phase 1)."""

from fastapi import Header, HTTPException, status

from app.api.routes.v2.auth import decode_jwt
from app.config import settings


def _valid_api_keys() -> set[str]:
    return set(settings.api_key_list)


async def get_current_user_v2(
    authorization: str | None = Header(None),
    homebot_api_key: str | None = Header(None, alias="HOMEBOT-API-KEY"),
) -> str:
    """Require valid JWT (Bearer) or HOMEBOT-API-KEY header. Returns principal (email or 'api-key')."""
    # Try JWT first
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        payload = decode_jwt(token)
        if payload and "sub" in payload:
            return payload["sub"]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    # Try API key
    if homebot_api_key and homebot_api_key.strip():
        if homebot_api_key.strip() in _valid_api_keys():
            return "api-key"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required (Bearer token or HOMEBOT-API-KEY header)",
    )


async def require_api_key(
    homebot_api_key: str | None = Header(None, alias="HOMEBOT-API-KEY"),
) -> str:
    """Require valid HOMEBOT-API-KEY header. Use for service account endpoints."""
    if not homebot_api_key or not homebot_api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing HOMEBOT-API-KEY header",
        )
    if homebot_api_key.strip() not in _valid_api_keys():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return "api-key"
