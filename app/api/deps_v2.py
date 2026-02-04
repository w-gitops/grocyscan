"""API v2 dependencies: JWT and API key auth (Phase 1), tenant context (Phase 2)."""

import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.v2.auth import decode_jwt
from app.config import settings
from app.db.database import get_db


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


async def get_tenant_id_v2(
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
) -> uuid.UUID:
    """Require X-Tenant-ID header for v2 inventory APIs (RLS context)."""
    if not x_tenant_id or not x_tenant_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID header required",
        )
    try:
        return uuid.UUID(x_tenant_id.strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Tenant-ID format",
        ) from None


async def get_db_homebot(
    tenant_id: uuid.UUID = Depends(get_tenant_id_v2),
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[AsyncSession, None]:
    """Database session with app.tenant_id set for RLS."""
    # PostgreSQL SET LOCAL requires literal value, not bound param
    await db.execute(text(f"SET LOCAL app.tenant_id = '{str(tenant_id).replace(chr(39), chr(39)+chr(39))}'"))
    yield db


async def get_device_fingerprint(
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> str:
    """Require X-Device-ID header (device fingerprint) for device/me endpoints."""
    if not x_device_id or not x_device_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Device-ID header required",
        )
    return x_device_id.strip()
