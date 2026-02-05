"""Session-based /api/me endpoints for Vue frontend.

Uses session cookie auth; requires X-Device-ID header for device operations.
Resolves tenant from first tenant in DB (single-tenant default).
"""

import re
import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.homebot_models import (
    HomebotBarcode,
    HomebotDevice,
    HomebotLocation,
    HomebotProduct,
    HomebotStock,
    HomebotStockTransaction,
)
from app.schemas.v2.device import DeviceCreate, DeviceResponse, DeviceUpdatePreferences
from app.schemas.v2.location import LocationResponse
from app.schemas.v2.product import ProductResponse, ProductUpdate
from app.schemas.v2.stock import StockEntryResponse

router = APIRouter()


def _set_tenant_id_stmt(tenant_id: uuid.UUID):  # noqa: ANN201
    """Return SET LOCAL statement; value must be literal (PostgreSQL does not allow params)."""
    tid = str(tenant_id).replace("'", "''")
    return text(f"SET LOCAL app.tenant_id = '{tid}'")


class MeStockAddBody(BaseModel):
    """Session stock add request."""

    product_id: UUID
    quantity: int = Field(..., gt=0)
    location_id: UUID | None = None


class MeProductCreate(BaseModel):
    """Create product (and optionally add initial stock) for /api/me/products."""

    name: str = Field(..., min_length=1, max_length=500)
    barcode: str | None = Field(None, max_length=100)
    description: str | None = None
    category: str | None = None
    quantity_unit: str | None = None
    min_stock_quantity: int = Field(default=0, ge=0)
    quantity: int = Field(default=0, ge=0, description="Initial stock to add (0 = no stock)")
    location_id: UUID | None = None


class MeBarcodeAdd(BaseModel):
    """Add barcode to product for /api/me/products/{id}/barcodes."""

    barcode: str = Field(..., min_length=1, max_length=100)


class MeStockConsumeBody(BaseModel):
    """Session stock consume request."""

    product_id: UUID
    quantity: int = Field(..., gt=0)
    location_id: UUID | None = None


# Fixed UUID for default tenant (matches migration 0007); used to seed when missing.
_DEFAULT_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def _ensure_default_tenant(db: AsyncSession) -> uuid.UUID | None:
    """Insert default tenant if none exists (idempotent); return its id or None on failure."""
    try:
        await db.execute(
            text("""
                INSERT INTO homebot.tenants (id, name, slug, settings, created_at, updated_at)
                VALUES (
                    :tid::uuid,
                    'Default',
                    'default',
                    NULL,
                    now(),
                    now()
                )
                ON CONFLICT (id) DO NOTHING
            """),
            {"tid": str(_DEFAULT_TENANT_ID)},
        )
        await db.commit()
    except Exception:
        await db.rollback()
        return None
    return _DEFAULT_TENANT_ID


async def _get_default_tenant_id(db: AsyncSession) -> uuid.UUID | None:
    """Get first tenant id (homebot.tenants has SELECT policy with true)."""
    result = await db.execute(text("SELECT id FROM homebot.tenants LIMIT 1"))
    row = result.scalar_one_or_none()
    # scalar_one_or_none() returns the single column value (UUID) with asyncpg, not a Row
    if row is not None:
        return row[0] if hasattr(row, "__getitem__") else row
    # No tenant: try to seed default tenant so device registration works without running 0007.
    await _ensure_default_tenant(db)
    result = await db.execute(text("SELECT id FROM homebot.tenants LIMIT 1"))
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return row[0] if hasattr(row, "__getitem__") else row


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
        await session.execute(_set_tenant_id_stmt(tenant_id))
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
        await session.execute(_set_tenant_id_stmt(tenant_id))
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
        await session.execute(_set_tenant_id_stmt(tenant_id))
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
        await session.execute(_set_tenant_id_stmt(tenant_id))
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


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product_me(
    request: Request,
    body: MeProductCreate,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> ProductResponse:
    """Create a product for device tenant. Optionally link barcode and add initial stock (session auth)."""
    async for session, tenant_id, device in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))
        name_normalized = _normalize_name(body.name) or None
        product = HomebotProduct(
            tenant_id=tenant_id,
            name=body.name,
            name_normalized=name_normalized,
            description=body.description,
            category=body.category,
            quantity_unit=body.quantity_unit,
            min_stock_quantity=body.min_stock_quantity,
            attributes={},
        )
        session.add(product)
        await session.flush()
        if body.barcode and body.barcode.strip():
            session.add(
                HomebotBarcode(
                    tenant_id=tenant_id,
                    product_id=product.id,
                    barcode=body.barcode.strip(),
                    is_primary=True,
                )
            )
        if body.quantity > 0:
            location_id = body.location_id or device.default_location_id
            if location_id:
                r = await session.execute(
                    select(HomebotStock).where(
                        HomebotStock.tenant_id == tenant_id,
                        HomebotStock.product_id == product.id,
                        HomebotStock.location_id == location_id,
                    )
                )
                row = r.scalar_one_or_none()
                if row:
                    row.quantity += body.quantity
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
                        product_id=product.id,
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
        await session.refresh(product)
        barcodes = [body.barcode.strip()] if body.barcode and body.barcode.strip() else []
        data = ProductResponse.model_validate(product).model_dump()
        data["barcodes"] = barcodes
        return ProductResponse(**data)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.get("/products", response_model=list[ProductResponse])
async def list_products_me(
    request: Request,
    q: str | None = None,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> list[ProductResponse]:
    """List homebot products for device tenant (session auth). Optional ?q= search. Includes barcodes."""
    async for session, tenant_id, _ in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))
        stmt = select(HomebotProduct).where(HomebotProduct.deleted_at.is_(None))
        if q and q.strip():
            pattern = f"%{q.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    HomebotProduct.name.ilike(pattern),
                    HomebotProduct.name_normalized.ilike(pattern),
                )
            )
        result = await session.execute(stmt)
        products = result.scalars().unique().all()
        if not products:
            return []
        product_ids = [p.id for p in products]
        barcode_r = await session.execute(
            select(HomebotBarcode.product_id, HomebotBarcode.barcode).where(
                HomebotBarcode.product_id.in_(product_ids)
            )
        )
        barcodes_by_product: dict = {pid: [] for pid in product_ids}
        for row in barcode_r.all():
            barcodes_by_product.setdefault(row[0], []).append(row[1])
        out = []
        for p in products:
            data = {
                "id": p.id,
                "tenant_id": p.tenant_id,
                "name": p.name,
                "name_normalized": getattr(p, "name_normalized", None),
                "description": p.description,
                "category": p.category,
                "quantity_unit": getattr(p, "quantity_unit", None),
                "min_stock_quantity": getattr(p, "min_stock_quantity", 0) or 0,
                "attributes": getattr(p, "attributes", None),
                "barcodes": barcodes_by_product.get(p.id, []),
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            }
            out.append(ProductResponse.model_validate(data))
        return out
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.get("/products/{product_id}")
async def get_product_detail_me(
    product_id: UUID,
    request: Request,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> dict:
    """Product detail with stock per location (session auth)."""
    async for session, tenant_id, _ in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))
        r = await session.execute(
            select(HomebotProduct).where(
                HomebotProduct.id == product_id,
                HomebotProduct.deleted_at.is_(None),
            )
        )
        product = r.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        # Stock rows with location name
        stock_r = await session.execute(
            select(HomebotStock, HomebotLocation)
            .outerjoin(HomebotLocation, HomebotStock.location_id == HomebotLocation.id)
            .where(
                HomebotStock.tenant_id == tenant_id,
                HomebotStock.product_id == product_id,
                HomebotStock.quantity > 0,
            )
        )
        stock_list = [
            {
                "id": str(row[0].id),
                "location_id": str(row[0].location_id) if row[0].location_id else None,
                "location_name": row[1].name if row[1] else "Unspecified",
                "quantity": row[0].quantity,
                "expiration_date": str(row[0].expiration_date) if row[0].expiration_date else None,
                "stock_id": row[0].stock_id,
                "price": float(row[0].price) if row[0].price else None,
                "open": row[0].open,
                "opened_date": str(row[0].opened_date) if row[0].opened_date else None,
                "note": row[0].note,
            }
            for row in stock_r.all()
        ]
        barcode_r = await session.execute(
            select(HomebotBarcode.barcode).where(HomebotBarcode.product_id == product_id)
        )
        barcodes = [r[0] for r in barcode_r.all()]
        product_resp = ProductResponse.model_validate(product).model_dump() | {"barcodes": barcodes}
        return {
            "product": ProductResponse(**product_resp),
            "stock": stock_list,
        }
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


def _normalize_name(name: str) -> str:
    """Lowercase and collapse whitespace for search."""
    return re.sub(r"\s+", " ", name.lower().strip()) if name else ""


@router.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product_me(
    product_id: UUID,
    body: ProductUpdate,
    request: Request,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> ProductResponse:
    """Update product (partial, session auth)."""
    async for session, tenant_id, _ in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))
        r = await session.execute(
            select(HomebotProduct).where(
                HomebotProduct.id == product_id,
                HomebotProduct.deleted_at.is_(None),
            )
        )
        product = r.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        data = body.model_dump(exclude_unset=True)
        if "name" in data and data["name"]:
            data["name_normalized"] = _normalize_name(data["name"]) or None
        for key, value in data.items():
            setattr(product, key, value)
        await session.commit()
        await session.refresh(product)
        barcode_r = await session.execute(select(HomebotBarcode.barcode).where(HomebotBarcode.product_id == product_id))
        barcodes = [row[0] for row in barcode_r.all()]
        resp_data = ProductResponse.model_validate(product).model_dump()
        resp_data["barcodes"] = barcodes
        return ProductResponse(**resp_data)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.post("/products/{product_id}/barcodes", status_code=status.HTTP_201_CREATED)
async def add_product_barcode_me(
    product_id: UUID,
    body: MeBarcodeAdd,
    request: Request,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> dict[str, str]:
    """Add a barcode to a product (session auth). Fails if barcode already linked to another product."""
    async for session, tenant_id, _ in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))
        r = await session.execute(
            select(HomebotProduct).where(
                HomebotProduct.id == product_id,
                HomebotProduct.deleted_at.is_(None),
            )
        )
        if not r.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        barcode_str = body.barcode.strip()
        existing = await session.execute(
            select(HomebotBarcode).where(
                HomebotBarcode.tenant_id == tenant_id,
                HomebotBarcode.barcode == barcode_str,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Barcode already linked to another product",
            )
        session.add(
            HomebotBarcode(
                tenant_id=tenant_id,
                product_id=product_id,
                barcode=barcode_str,
                is_primary=False,
            )
        )
        await session.commit()
        return {"status": "ok", "barcode": barcode_str}
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.delete("/products/{product_id}/barcodes/{barcode:path}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_product_barcode_me(
    product_id: UUID,
    barcode: str,
    request: Request,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> None:
    """Remove a barcode from a product (session auth)."""
    async for session, tenant_id, _ in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))
        result = await session.execute(
            select(HomebotBarcode).where(
                HomebotBarcode.tenant_id == tenant_id,
                HomebotBarcode.product_id == product_id,
                HomebotBarcode.barcode == barcode.strip(),
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barcode not found for this product")
        await session.delete(row)
        await session.commit()
        return
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.get("/stock", response_model=list[StockEntryResponse])
async def list_stock_me(
    request: Request,
    product_id: UUID | None = None,
    location_id: UUID | None = None,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> list[StockEntryResponse]:
    """List stock entries for device tenant (inventory overview). Optional product_id, location_id query params."""
    async for session, tenant_id, _ in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))
        stmt = (
            select(HomebotStock, HomebotProduct.name, HomebotLocation.name)
            .join(HomebotProduct, HomebotStock.product_id == HomebotProduct.id)
            .outerjoin(HomebotLocation, HomebotStock.location_id == HomebotLocation.id)
            .where(HomebotProduct.deleted_at.is_(None))
        )
        if product_id is not None:
            stmt = stmt.where(HomebotStock.product_id == product_id)
        if location_id is not None:
            stmt = stmt.where(HomebotStock.location_id == location_id)
        stmt = stmt.order_by(HomebotProduct.name, HomebotLocation.name.asc().nulls_last())
        result = await session.execute(stmt)
        rows = result.all()
        return [
            StockEntryResponse(
                id=row[0].id,
                product_id=row[0].product_id,
                product_name=row[1],
                location_id=row[0].location_id,
                location_name=row[2],
                quantity=row[0].quantity,
                expiration_date=row[0].expiration_date,
                created_at=row[0].created_at,
                updated_at=row[0].updated_at,
            )
            for row in rows
        ]
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.get("/locations", response_model=list[LocationResponse])
async def list_locations_me(
    request: Request,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> list[LocationResponse]:
    """List homebot locations for device tenant (session auth)."""
    async for session, tenant_id, _ in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))
        result = await session.execute(
            select(HomebotLocation).where(HomebotLocation.tenant_id == tenant_id).order_by(HomebotLocation.sort_order, HomebotLocation.name)
        )
        locations = result.scalars().unique().all()
        return [LocationResponse.model_validate(loc) for loc in locations]
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


class MeLocationCreate(BaseModel):
    """Create location request for /api/me/locations."""

    name: str = Field(..., min_length=1, max_length=255)
    location_type: str = Field(default="shelf", max_length=50)
    parent_id: UUID | None = None
    description: str | None = None
    is_freezer: bool = False
    sort_order: int = 0


class MeLocationUpdate(BaseModel):
    """Update location request for /api/me/locations/{id}."""

    name: str | None = Field(None, min_length=1, max_length=255)
    location_type: str | None = Field(None, max_length=50)
    parent_id: UUID | None = None
    description: str | None = None
    is_freezer: bool | None = None
    sort_order: int | None = None


@router.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location_me(
    request: Request,
    body: MeLocationCreate,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> LocationResponse:
    """Create a homebot location for device tenant (session auth)."""
    from app.db.homebot_models import HomebotLocationClosure
    async for session, tenant_id, _ in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))

        # Validate parent if provided
        if body.parent_id:
            pr = await session.execute(
                select(HomebotLocation).where(
                    HomebotLocation.id == body.parent_id,
                    HomebotLocation.tenant_id == tenant_id,
                )
            )
            if not pr.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent location not found")

        loc = HomebotLocation(
            tenant_id=tenant_id,
            name=body.name,
            location_type=body.location_type,
            parent_id=body.parent_id,
            description=body.description,
            is_freezer=body.is_freezer,
            sort_order=body.sort_order,
        )
        session.add(loc)
        await session.flush()

        # Build closure table entries
        session.add(HomebotLocationClosure(ancestor_id=loc.id, descendant_id=loc.id, depth=0))
        if body.parent_id:
            # Add closure rows from all ancestors of parent to this new location
            result = await session.execute(
                select(HomebotLocationClosure.ancestor_id, HomebotLocationClosure.depth).where(
                    HomebotLocationClosure.descendant_id == body.parent_id
                )
            )
            for ancestor_id, depth in result.all():
                session.add(
                    HomebotLocationClosure(
                        ancestor_id=ancestor_id,
                        descendant_id=loc.id,
                        depth=depth + 1,
                    )
                )

        await session.commit()
        await session.refresh(loc)
        return LocationResponse.model_validate(loc)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.patch("/locations/{location_id}", response_model=LocationResponse)
async def update_location_me(
    location_id: UUID,
    request: Request,
    body: MeLocationUpdate,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> LocationResponse:
    """Update a homebot location (session auth)."""
    async for session, tenant_id, _ in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))
        r = await session.execute(
            select(HomebotLocation).where(
                HomebotLocation.id == location_id,
                HomebotLocation.tenant_id == tenant_id,
            )
        )
        loc = r.scalar_one_or_none()
        if not loc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

        data = body.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(loc, key, value)
        await session.commit()
        await session.refresh(loc)
        return LocationResponse.model_validate(loc)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location_me(
    location_id: UUID,
    request: Request,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> None:
    """Delete a homebot location (session auth). Fails if has children or stock."""
    from app.db.homebot_models import HomebotLocationClosure
    from sqlalchemy import delete
    async for session, tenant_id, _ in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))
        r = await session.execute(
            select(HomebotLocation).where(
                HomebotLocation.id == location_id,
                HomebotLocation.tenant_id == tenant_id,
            )
        )
        loc = r.scalar_one_or_none()
        if not loc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

        # Check for children
        cr = await session.execute(
            select(HomebotLocation).where(HomebotLocation.parent_id == location_id)
        )
        if cr.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete location with children")

        # Check for stock
        sr = await session.execute(
            select(HomebotStock).where(HomebotStock.location_id == location_id)
        )
        if sr.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete location with stock. Move or consume stock first.",
            )

        # Delete closure rows
        await session.execute(
            delete(HomebotLocationClosure).where(
                (HomebotLocationClosure.ancestor_id == location_id) | (HomebotLocationClosure.descendant_id == location_id)
            )
        )

        await session.delete(loc)
        await session.commit()
        return
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


# Phase 3.5 Stock Operations


class MeStockTransferBody(BaseModel):
    """Transfer stock request."""

    product_id: UUID
    from_location_id: UUID
    to_location_id: UUID
    quantity: int = Field(..., gt=0)


class MeStockInventoryBody(BaseModel):
    """Set stock to specific amount (inventory correction)."""

    product_id: UUID
    new_amount: int = Field(..., ge=0)
    location_id: UUID | None = None


class MeStockOpenBody(BaseModel):
    """Mark stock entry as opened."""

    stock_entry_id: UUID


class MeStockEntryEditBody(BaseModel):
    """Edit stock entry."""

    amount: int | None = Field(None, ge=0)
    location_id: UUID | None = None
    note: str | None = None
    open: bool | None = None


@router.post("/stock/transfer")
async def transfer_stock_me(
    request: Request,
    body: MeStockTransferBody,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> dict:
    """Transfer stock between locations (session auth)."""
    async for session, tenant_id, _ in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))

        # Get source stock
        r = await session.execute(
            select(HomebotStock).where(
                HomebotStock.tenant_id == tenant_id,
                HomebotStock.product_id == body.product_id,
                HomebotStock.location_id == body.from_location_id,
            )
        )
        from_row = r.scalar_one_or_none()
        if not from_row or from_row.quantity < body.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock at source location",
            )
        from_row.quantity -= body.quantity

        # Get or create destination stock
        r2 = await session.execute(
            select(HomebotStock).where(
                HomebotStock.tenant_id == tenant_id,
                HomebotStock.product_id == body.product_id,
                HomebotStock.location_id == body.to_location_id,
            )
        )
        to_row = r2.scalar_one_or_none()
        if to_row:
            to_row.quantity += body.quantity
        else:
            to_row = HomebotStock(
                tenant_id=tenant_id,
                product_id=body.product_id,
                location_id=body.to_location_id,
                quantity=body.quantity,
                stock_id=str(uuid.uuid4()),
            )
            session.add(to_row)
            await session.flush()

        # Create correlated transactions
        correlation_id = uuid.uuid4()
        session.add(
            HomebotStockTransaction(
                tenant_id=tenant_id,
                stock_id=from_row.id,
                product_id=body.product_id,
                transaction_type="transfer_from",
                quantity=-body.quantity,
                from_location_id=body.from_location_id,
                to_location_id=body.to_location_id,
                correlation_id=correlation_id,
            )
        )
        session.add(
            HomebotStockTransaction(
                tenant_id=tenant_id,
                stock_id=to_row.id,
                product_id=body.product_id,
                transaction_type="transfer_to",
                quantity=body.quantity,
                from_location_id=body.from_location_id,
                to_location_id=body.to_location_id,
                correlation_id=correlation_id,
            )
        )
        await session.commit()
        return {"status": "ok", "message": "Stock transferred"}
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.post("/stock/inventory")
async def inventory_stock_me(
    request: Request,
    body: MeStockInventoryBody,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> dict:
    """Set stock to specific amount (inventory correction, session auth)."""
    async for session, tenant_id, device in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))
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
            current = row.quantity
            diff = body.new_amount - current
            row.quantity = body.new_amount
            session.add(
                HomebotStockTransaction(
                    tenant_id=tenant_id,
                    stock_id=row.id,
                    product_id=body.product_id,
                    transaction_type="inventory-correction",
                    quantity=diff,
                    to_location_id=location_id,
                )
            )
        else:
            if body.new_amount <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot set non-existing stock to zero or negative",
                )
            row = HomebotStock(
                tenant_id=tenant_id,
                product_id=body.product_id,
                location_id=location_id,
                quantity=body.new_amount,
                stock_id=str(uuid.uuid4()),
            )
            session.add(row)
            await session.flush()
            session.add(
                HomebotStockTransaction(
                    tenant_id=tenant_id,
                    stock_id=row.id,
                    product_id=body.product_id,
                    transaction_type="inventory-correction",
                    quantity=body.new_amount,
                    to_location_id=location_id,
                )
            )
        await session.commit()
        await session.refresh(row)
        return {"status": "ok", "quantity": row.quantity}
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.post("/stock/open")
async def open_stock_me(
    request: Request,
    body: MeStockOpenBody,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> dict:
    """Mark stock entry as opened (session auth)."""
    from datetime import date as date_type

    async for session, tenant_id, _ in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))

        r = await session.execute(
            select(HomebotStock).where(
                HomebotStock.id == body.stock_entry_id,
                HomebotStock.tenant_id == tenant_id,
            )
        )
        row = r.scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock entry not found")
        if row.open:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stock entry already opened")

        row.open = True
        row.opened_date = date_type.today()

        session.add(
            HomebotStockTransaction(
                tenant_id=tenant_id,
                stock_id=row.id,
                product_id=row.product_id,
                transaction_type="product-opened",
                quantity=0,
            )
        )
        await session.commit()
        await session.refresh(row)
        return {"status": "ok", "open": True, "opened_date": str(row.opened_date)}
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.patch("/stock/entries/{entry_id}")
async def edit_stock_entry_me(
    entry_id: UUID,
    request: Request,
    body: MeStockEntryEditBody,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> dict:
    """Edit stock entry (session auth)."""
    from datetime import date as date_type

    async for session, tenant_id, _ in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))

        r = await session.execute(
            select(HomebotStock).where(
                HomebotStock.id == entry_id,
                HomebotStock.tenant_id == tenant_id,
            )
        )
        row = r.scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock entry not found")

        data = body.model_dump(exclude_unset=True)
        if "amount" in data and data["amount"] is not None:
            row.quantity = data["amount"]
        if "location_id" in data:
            row.location_id = data["location_id"]
        if "note" in data:
            row.note = data["note"]
        if "open" in data and data["open"] is not None:
            row.open = data["open"]
            if data["open"] and not row.opened_date:
                row.opened_date = date_type.today()

        correlation_id = uuid.uuid4()
        session.add(
            HomebotStockTransaction(
                tenant_id=tenant_id,
                stock_id=row.id,
                product_id=row.product_id,
                transaction_type="stock-edit",
                quantity=0,
                correlation_id=correlation_id,
                notes=str(data),
            )
        )

        await session.commit()
        await session.refresh(row)
        return {"status": "ok", "quantity": row.quantity}
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.post("/stock/undo/{transaction_id}")
async def undo_transaction_me(
    transaction_id: UUID,
    request: Request,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> dict:
    """Undo a stock transaction (session auth)."""
    async for session, tenant_id, _ in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))

        r = await session.execute(
            select(HomebotStockTransaction).where(
                HomebotStockTransaction.id == transaction_id,
                HomebotStockTransaction.tenant_id == tenant_id,
            )
        )
        tx = r.scalar_one_or_none()
        if not tx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        if tx.undone:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction already undone")

        # Get all related transactions via correlation_id
        transactions = [tx]
        if tx.correlation_id:
            cr = await session.execute(
                select(HomebotStockTransaction).where(
                    HomebotStockTransaction.correlation_id == tx.correlation_id,
                    HomebotStockTransaction.tenant_id == tenant_id,
                )
            )
            transactions = list(cr.scalars().all())

        now = datetime.now(timezone.utc)
        for t in transactions:
            if t.undone:
                continue

            # Reverse the effect on stock
            if t.stock_id and t.quantity != 0:
                sr = await session.execute(select(HomebotStock).where(HomebotStock.id == t.stock_id))
                stock = sr.scalar_one_or_none()
                if stock:
                    stock.quantity -= t.quantity

            # Mark as undone
            t.undone = True
            t.undone_timestamp = now

        await session.commit()
        return {"status": "ok", "message": f"Undone {len(transactions)} transaction(s)"}
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")


@router.get("/stock/transactions")
async def list_transactions_me(
    request: Request,
    product_id: UUID | None = None,
    limit: int = 100,
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
) -> list[dict]:
    """List stock transactions (audit log, session auth)."""
    async for session, tenant_id, _ in _session_device_context(request, x_device_id):
        await session.execute(_set_tenant_id_stmt(tenant_id))

        stmt = (
            select(HomebotStockTransaction)
            .where(HomebotStockTransaction.tenant_id == tenant_id)
            .order_by(HomebotStockTransaction.created_at.desc())
            .limit(limit)
        )
        if product_id:
            stmt = stmt.where(HomebotStockTransaction.product_id == product_id)

        result = await session.execute(stmt)
        transactions = result.scalars().all()
        return [
            {
                "id": str(t.id),
                "stock_id": str(t.stock_id) if t.stock_id else None,
                "product_id": str(t.product_id) if t.product_id else None,
                "transaction_type": t.transaction_type,
                "quantity": t.quantity,
                "from_location_id": str(t.from_location_id) if t.from_location_id else None,
                "to_location_id": str(t.to_location_id) if t.to_location_id else None,
                "notes": t.notes,
                "spoiled": t.spoiled,
                "correlation_id": str(t.correlation_id) if t.correlation_id else None,
                "undone": t.undone,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in transactions
        ]
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No session")
