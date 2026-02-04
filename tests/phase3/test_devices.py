"""Phase 3 device API tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_post_devices_requires_auth():
    """POST /api/v2/devices requires auth (no tenant to avoid DB)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.post(
            "/api/v2/devices",
            json={"name": "Kitchen Tablet", "fingerprint": "fp1", "device_type": "tablet"},
        )
    assert r.status_code in (400, 401)


@pytest.mark.asyncio
async def test_get_devices_me_requires_device_id():
    """GET /api/v2/devices/me requires X-Device-ID (no tenant to avoid DB)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/api/v2/devices/me")
    assert r.status_code in (400, 401)


@pytest.mark.asyncio
async def test_me_product_by_barcode_requires_auth_or_device_id():
    """GET /api/me/product-by-barcode/{code} requires session + X-Device-ID."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/api/me/product-by-barcode/123456")
    assert r.status_code in (400, 401)


@pytest.mark.asyncio
async def test_me_stock_add_requires_auth_or_device_id():
    """POST /api/me/stock/add requires session + X-Device-ID."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.post(
            "/api/me/stock/add",
            json={"product_id": "00000000-0000-0000-0000-000000000001", "quantity": 1},
        )
    assert r.status_code in (400, 401)
