"""Phase 2 stock API tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_add_stock_requires_auth():
    """POST /api/v2/stock/add requires auth (no X-Tenant-ID to avoid DB)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.post(
            "/api/v2/stock/add",
            json={
                "product_id": "00000000-0000-0000-0000-000000000002",
                "quantity": 1,
            },
        )
    assert r.status_code in (400, 401)
