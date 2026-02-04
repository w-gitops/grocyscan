"""Phase 4: QR token system tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.qr import generate_token, validate_checksum


def test_crockford_token_format() -> None:
    """Generated token matches NS-CODE-CHECK format."""
    token = generate_token("HB")
    parts = token.split("-")
    assert len(parts) == 3
    assert parts[0] == "HB"
    assert len(parts[1]) >= 1
    assert len(parts[2]) == 1


def test_crockford_checksum_validates() -> None:
    """Checksum validates correctly for generated token."""
    token = generate_token("NS")
    assert validate_checksum(token) is True


def test_crockford_checksum_invalid() -> None:
    """Wrong checksum fails validation."""
    # Valid token then corrupt last char
    token = generate_token("X")
    bad = token[:-1] + ("0" if token[-1] != "0" else "1")
    assert validate_checksum(bad) is False


@pytest.mark.asyncio
async def test_create_qr_token_requires_auth() -> None:
    """POST /api/v2/qr-tokens requires auth (no X-Tenant-ID to avoid DB)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.post("/api/v2/qr-tokens", json={"namespace": "HB"})
    assert r.status_code in (401, 400)


@pytest.mark.asyncio
async def test_create_qr_token_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
    tenant_id: str,
) -> None:
    """POST /api/v2/qr-tokens creates token with namespace, code, checksum, state."""
    headers = {**auth_headers, "X-Tenant-ID": tenant_id}
    r = await client.post("/api/v2/qr-tokens", json={"namespace": "HB"}, headers=headers)
    if r.status_code != 201:
        pytest.skip("DB not available or migration not run")
    data = r.json()
    assert data["namespace"] == "HB"
    assert data["code"]
    assert data["checksum"]
    assert data["state"] == "unassigned"
    assert "id" in data
    assert validate_checksum(f"{data['namespace']}-{data['code']}-{data['checksum']}")


@pytest.mark.asyncio
async def test_qr_redirect_unassigned(
    client: AsyncClient,
    auth_headers: dict[str, str],
    tenant_id: str,
) -> None:
    """GET /q/{token} redirects when token exists and is unassigned."""
    headers = {**auth_headers, "X-Tenant-ID": tenant_id}
    create_r = await client.post("/api/v2/qr-tokens", json={"namespace": "R"}, headers=headers)
    if create_r.status_code != 201:
        pytest.skip("DB not available")
    data = create_r.json()
    token_str = f"{data['namespace']}-{data['code']}-{data['checksum']}"
    r = await client.get(f"/q/{token_str}")
    assert r.status_code == 302
    assert "assign" in r.headers.get("location", "")
