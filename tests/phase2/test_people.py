"""Phase 2 people API tests."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_list_people_requires_auth():
    """GET /api/v2/people requires auth (and X-Tenant-ID)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/api/v2/people")
    assert r.status_code in (400, 401)


@pytest.mark.asyncio
async def test_create_person_requires_tenant_header(client, auth_headers):
    """POST /api/v2/people requires X-Tenant-ID header."""
    r = await client.post(
        "/api/v2/people",
        json={"name": "Alex"},
        headers=auth_headers,
    )
    assert r.status_code == 400
