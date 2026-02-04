"""Phase 2 product API tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_create_product_requires_tenant_and_auth():
    """POST /api/v2/products requires X-Tenant-ID and auth."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.post(
            "/api/v2/products",
            json={"name": "Milk"},
        )
    assert r.status_code in (401, 400)  # 401 no auth or 400 missing tenant


@pytest.mark.asyncio
async def test_list_products_requires_auth():
    """GET /api/v2/products requires auth (no X-Tenant-ID to avoid DB)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/api/v2/products")
    assert r.status_code in (400, 401)
