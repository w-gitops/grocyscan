"""Phase 2 location API tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_list_locations_requires_auth():
    """GET /api/v2/locations requires auth (no X-Tenant-ID to avoid DB)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/api/v2/locations")
    assert r.status_code in (400, 401)
