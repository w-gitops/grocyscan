"""Session-based /api/me endpoints for NiceGUI (Phase 3 Option A).

Uses session cookie auth; requires X-Device-ID header for device operations.
Resolves tenant from first tenant in DB (single-tenant default).
"""

import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.homebot_models import (
    HomebotBarcode,
    HomebotDevice,
    HomebotProduct,
    HomebotStock,
    HomebotStockTransaction,
)
from app.schemas.v2.device import DeviceCreate, DeviceResponse, DeviceUpdatePreferences

router = APIRouter()


class MeStockAddBody(BaseModel):
    """Session stock add request."""

    product_id: UUID
    quantity: int = Field(..., gt=0)
    location_id: UUID | None = None


class MeStockConsumeBody(BaseModel):
    """Session stock consume request."""

    product_id: UUID
    quantity: int = Field(..., gt=0)
    location_id: UUID | None = None


async def _get_default_tenant_id(db: AsyncSession) -> uuid.UUID | None:
    """Get first tenant id (homebot.tenants has SELECT policy with true)."""
    result = await db.execute(text("SELECT id FROM homebot.tenants LIMIT 1"))
    row = result.scalar_one_or_none()
    return row[0] if row else None


async def _set_tenant_and_get_device_session(
    request: Request,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> AsyncSession:
    """Require session auth and X-Device-ID; return db session with tenant set."""
    if not getattr(request.state, "user_id", None):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if not x_device_id or not x_device_id.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Device-ID header required")
    # Get a db session (from get_db dependency we need to inject differently - we'll get it in route)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Use get_me_device_session")


async def get_me_device_session(
    request: Request,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
    db: AsyncSession = None,
) -> tuple[AsyncSession, str]:
    """Dependency: require session + X-Device-ID, set tenant on db, return (db, fingerprint)."""
    from app.db.database import get_db
    # We need to use Depends(get_db) in the route and then run tenant + return fingerprint
    # So this dependency can't easily do async get_db. Instead do it in the route.
    if not getattr(request.state, "user_id", None):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if not x_device_id or not x_device_id.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Device-ID header required")
    return db, x_device_id.strip()


# We'll use a single dependency that gets db, sets tenant, and returns (db, fingerprint)
# by having the route call a helper that takes db and request.
def _require_session_and_device_id(request: Request, x_device_id: str | None) -> str:
    """Raise if not authenticated or missing X-Device-ID; return fingerprint."""
    if not getattr(request.state, "user_id", None):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if not x_device_id or not x_device_id.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Device-ID header required")
    return x_device_id.strip()


@router.post("/device", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device_me(
    request: Request,
    body: DeviceCreate,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> DeviceResponse:
    """Register device (session auth). Body name/device_type; fingerprint from X-Device-ID."""
    from app.db.database import get_db
    fingerprint = _require_session_and_device_id(request, x_device_id)
    # Use body fingerprint if provided, else header
    fp = body.fingerprint.strip() if body.fingerprint else fingerprint
    async for session in get_db():
        tenant_id = await _get_default_tenant_id(session)
        if not tenant_id:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No tenant configured")
        await session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": str(tenant_id)})
        result = await session.execute(
            select(HomebotDevice).where(
                HomebotDevice.tenant_id == tenant_id,
                HomebotDevice.fingerprint == fp,
            )
        )
        device = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if device:
            device.name = body.name
            device.device_type = body.device_type
            device.last_seen_at = now
            await session.commit()
            await session.refresh(device)
            return DeviceResponse.model_validate(device)
        device = HomebotDevice(
            tenant_id=tenant_id,
            name=body.name,
            fingerprint=fp,
            device_type=body.device_type,
            last_seen_at=now,
        )
        session.add(device)
        await session.commit()
        await session.refresh(device)
        return DeviceResponse.model_validate(device)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.get("/device", response_model=DeviceResponse)
async def get_device_me(
    request: Request,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> DeviceResponse:
    """Get current device (session auth)."""
    from app.db.database import get_db
    fingerprint = _require_session_and_device_id(request, x_device_id)
    async for session in get_db():
        tenant_id = await _get_default_tenant_id(session)
        if not tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not registered")
        await session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": str(tenant_id)})
        result = await session.execute(
            select(HomebotDevice).where(HomebotDevice.fingerprint == fingerprint)
        )
        device = result.scalar_one_or_none()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not registered")
        return DeviceResponse.model_validate(device)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.patch("/device", response_model=DeviceResponse)
async def update_device_me(
    request: Request,
    body: DeviceUpdatePreferences,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> DeviceResponse:
    """Update device preferences (session auth)."""
    from app.db.database import get_db
    fingerprint = _require_session_and_device_id(request, x_device_id)
    async for session in get_db():
        tenant_id = await _get_default_tenant_id(session)
        if not tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not registered")
        await session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": str(tenant_id)})
        result = await session.execute(
            select(HomebotDevice).where(HomebotDevice.fingerprint == fingerprint)
        )
        device = result.scalar_one_or_none()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not registered")
        data = body.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(device, key, value)
        await session.commit()
        await session.refresh(device)
        return DeviceResponse.model_validate(device)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


async def _session_device_context(request: Request, x_device_id: str | None):
    """Yield (session, tenant_id, device) for session-authenticated device routes. Single get_db loop."""
    fingerprint = _require_session_and_device_id(request, x_device_id)
    async for session in get_db():
        tenant_id = await _get_default_tenant_id(session)
        if not tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No tenant configured")
        await session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": str(tenant_id)})
        result = await session.execute(
            select(HomebotDevice).where(HomebotDevice.fingerprint == fingerprint)
        )
        device = result.scalar_one_or_none()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not registered")
        yield session, tenant_id, device
        return
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.get("/product-by-barcode/{code}")
async def get_product_by_barcode_me(
    code: str,
    request: Request,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> dict:
    """Resolve barcode to homebot product (session auth). Returns 404 if not in inventory."""
    if not code or not code.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Barcode required")
    code = code.strip()
    async for session, tenant_id, _ in _session_device_context(request, x_device_id):
        result = await session.execute(
            select(HomebotBarcode, HomebotProduct)
            .join(HomebotProduct, HomebotBarcode.product_id == HomebotProduct.id)
            .where(
                HomebotBarcode.tenant_id == tenant_id,
                HomebotBarcode.barcode == code,
                HomebotProduct.deleted_at.is_(None),
            )
        )
        row = result.first()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found for barcode",
            )
        _barcode_row, product = row
        return {"product_id": str(product.id), "name": product.name}
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.post("/stock/add")
async def add_stock_me(
    request: Request,
    body: MeStockAddBody,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> dict:
    """Add stock (session auth). Uses device tenant and optional default location."""
    async for session, tenant_id, device in _session_device_context(request, x_device_id):
        location_id = body.location_id or device.default_location_id
        r = await session.execute(
            select(HomebotStock).where(
                HomebotStock.tenant_id == tenant_id,
                HomebotStock.product_id == body.product_id,
                HomebotStock.location_id == location_id,
            )
        )
        row = r.scalar_one_or_none()
        if row:
            row.quantity += body.quantity
            await session.flush()
            session.add(
                HomebotStockTransaction(
                    tenant_id=tenant_id,
                    stock_id=row.id,
                    transaction_type="add",
                    quantity=body.quantity,
                    to_location_id=location_id,
                )
            )
        else:
            row = HomebotStock(
                tenant_id=tenant_id,
                product_id=body.product_id,
                location_id=location_id,
                quantity=body.quantity,
            )
            session.add(row)
            await session.flush()
            session.add(
                HomebotStockTransaction(
                    tenant_id=tenant_id,
                    stock_id=row.id,
                    transaction_type="add",
                    quantity=body.quantity,
                    to_location_id=location_id,
                )
            )
        await session.commit()
        await session.refresh(row)
        return {"status": "ok", "quantity": row.quantity}
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.post("/stock/consume")
async def consume_stock_me(
    request: Request,
    body: MeStockConsumeBody,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> dict:
    """Consume stock (session auth)."""
    async for session, tenant_id, device in _session_device_context(request, x_device_id):
        del device  # unused
        stmt = select(HomebotStock).where(
            HomebotStock.tenant_id == tenant_id,
            HomebotStock.product_id == body.product_id,
            HomebotStock.quantity > 0,
        )
        if body.location_id is not None:
            stmt = stmt.where(HomebotStock.location_id == body.location_id)
        r = await session.execute(
            stmt.order_by(HomebotStock.expiration_date.asc().nulls_last())
        )
        rows = list(r.scalars().all())
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No stock found for product",
            )
        remaining = body.quantity
        for row in rows:
            if remaining <= 0:
                break
            take = min(remaining, row.quantity)
            row.quantity -= take
            remaining -= take
            session.add(
                HomebotStockTransaction(
                    tenant_id=tenant_id,
                    stock_id=row.id,
                    transaction_type="consume",
                    quantity=-take,
                )
            )
        if remaining > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock",
            )
        await session.commit()
        return {"status": "ok", "message": "Stock consumed"}
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")
