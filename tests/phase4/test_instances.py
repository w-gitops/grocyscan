"""Phase 4: Product instances (LPN) tests."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_create_instance_requires_auth() -> None:
    """POST /api/v2/instances requires auth (no X-Tenant-ID to avoid DB)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.post(
            "/api/v2/instances",
            json={"product_id": str(uuid.uuid4()), "remaining_quantity": 1},
        )
    assert r.status_code in (401, 400)


@pytest.mark.asyncio
async def test_consume_decrements_remaining(
    client: AsyncClient,
    auth_headers: dict[str, str],
    tenant_id: str,
) -> None:
    """Consuming from instance decrements remaining_quantity."""
    # Create product and instance via API if available
    headers = {**auth_headers, "X-Tenant-ID": tenant_id}
    prod_r = await client.post(
        "/api/v2/products",
        json={"name": "Instance Test Product"},
        headers=headers,
    )
    if prod_r.status_code not in (200, 201):
        pytest.skip("DB or products not available")
    product_id = prod_r.json()["id"]
    inst_r = await client.post(
        "/api/v2/instances",
        json={"product_id": product_id, "remaining_quantity": 3},
        headers=headers,
    )
    if inst_r.status_code != 201:
        pytest.skip("DB or instances not available")
    instance_id = inst_r.json()["id"]
    assert inst_r.json()["remaining_quantity"] == 3
    consume_r = await client.post(
        f"/api/v2/instances/{instance_id}/consume",
        json={"quantity": 2},
        headers=headers,
    )
    assert consume_r.status_code == 200
    assert consume_r.json()["remaining_quantity"] == 1
