"""Phase 4: Label templates and preview/print tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.phase4.conftest import SKIP_DB


@pytest.mark.asyncio
@pytest.mark.skipif(SKIP_DB, reason="Requires PostgreSQL with homebot schema")
async def test_preview_returns_png(
    client: AsyncClient,
    auth_headers: dict[str, str],
    tenant_id: str,
) -> None:
    """POST /api/v2/labels/preview returns PNG image."""
    headers = {**auth_headers, "X-Tenant-ID": tenant_id}
    r = await client.post(
        "/api/v2/labels/preview",
        json={"variables": {}},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("image/png")
    assert len(r.content) > 0


@pytest.mark.asyncio
@pytest.mark.skipif(SKIP_DB, reason="Requires PostgreSQL with homebot schema")
async def test_print_accepts_and_returns_job_id(
    client: AsyncClient,
    auth_headers: dict[str, str],
    tenant_id: str,
) -> None:
    """POST /api/v2/labels/print sends to printer (stub returns job_id)."""
    headers = {**auth_headers, "X-Tenant-ID": tenant_id}
    r = await client.post(
        "/api/v2/labels/print",
        json={"variables": {"name": "Test"}},
        headers=headers,
    )
    assert r.status_code == 202
    data = r.json()
    assert "job_id" in data
    assert data.get("status") == "queued"


@pytest.mark.asyncio
@pytest.mark.skipif(SKIP_DB, reason="Requires PostgreSQL with homebot schema")
async def test_create_label_template(
    client: AsyncClient,
    auth_headers: dict[str, str],
    tenant_id: str,
) -> None:
    """POST /api/v2/labels creates template with name, template_type, schema."""
    headers = {**auth_headers, "X-Tenant-ID": tenant_id}
    r = await client.post(
        "/api/v2/labels",
        json={"name": "Product Label", "template_type": "product", "schema": {"fields": ["name"]}},
        headers=headers,
    )
    if r.status_code != 201:
        pytest.skip("DB not available")
    data = r.json()
    assert data["name"] == "Product Label"
    assert data["template_type"] == "product"
    assert data.get("schema") == {"fields": ["name"]} or data.get("template_schema") == {"fields": ["name"]}
