"""Phase 2 inventory flow tests (v2 API with auth + tenant).

Skip when DATABASE_URL is not set to PostgreSQL with homebot schema.
"""

import os
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app

DATABASE_URL = os.environ.get("DATABASE_URL", "")
SKIP_DB = "postgresql" not in DATABASE_URL or "homebot" not in DATABASE_URL


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client):
    """JWT auth headers; patch settings in both auth route and services.auth so encode/decode use same secret."""
    from unittest.mock import MagicMock, patch

    from app.services.auth import hash_password

    mock_settings = MagicMock()
    mock_settings.auth_username = "test@test.com"
    mock_settings.auth_password_hash.get_secret_value.return_value = hash_password("secret")
    mock_settings.secret_key = "test-secret"
    with (
        patch("app.api.routes.v2.auth.settings", mock_settings),
        patch("app.services.auth.settings", mock_settings),
    ):
        r = await client.post(
            "/api/v2/auth/login",
            json={"email": "test@test.com", "password": "secret"},
        )
        assert r.status_code == 200
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
    # Yield from inside patch so decode_jwt (used by get_current_user_v2) sees same secret
    with (
        patch("app.api.routes.v2.auth.settings", mock_settings),
        patch("app.services.auth.settings", mock_settings),
    ):
        yield headers


@pytest.fixture
def tenant_id():
    return "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
@pytest.mark.skipif(SKIP_DB, reason="Requires PostgreSQL with homebot schema")
async def test_list_stock_requires_auth(client):
    """GET /api/v2/stock requires auth and X-Tenant-ID."""
    r = await client.get("/api/v2/stock")
    assert r.status_code in (400, 401)


@pytest.mark.asyncio
@pytest.mark.skipif(SKIP_DB, reason="Requires PostgreSQL with homebot schema")
async def test_list_stock_success(client, auth_headers, tenant_id):
    """GET /api/v2/stock with auth and tenant returns list (possibly empty)."""
    headers = {**auth_headers, "X-Tenant-ID": tenant_id}
    r = await client.get("/api/v2/stock", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
@pytest.mark.skipif(SKIP_DB, reason="Requires PostgreSQL with homebot schema")
async def test_create_product_list_products_get_product(client, auth_headers, tenant_id):
    """Create product via v2, list products, get product by id."""
    headers = {**auth_headers, "X-Tenant-ID": tenant_id}
    create = await client.post(
        "/api/v2/products",
        headers=headers,
        json={"name": "Test Product Phase2", "description": "For flow test"},
    )
    assert create.status_code == 201
    product = create.json()
    pid = product["id"]
    assert product["name"] == "Test Product Phase2"

    list_r = await client.get("/api/v2/products", headers=headers)
    assert list_r.status_code == 200
    products = list_r.json()
    ids = [p["id"] for p in products]
    assert pid in ids

    get_r = await client.get(f"/api/v2/products/{pid}", headers=headers)
    assert get_r.status_code == 200
    assert get_r.json()["name"] == "Test Product Phase2"
    assert "barcodes" in get_r.json()


@pytest.mark.asyncio
@pytest.mark.skipif(SKIP_DB, reason="Requires PostgreSQL with homebot schema")
async def test_add_stock_list_stock_consume(client, auth_headers, tenant_id):
    """Create product, create location, add stock, list stock, consume."""
    headers = {**auth_headers, "X-Tenant-ID": tenant_id}
    # Create location
    loc_r = await client.post(
        "/api/v2/locations",
        headers=headers,
        json={"name": "Test Shelf Phase2", "location_type": "shelf"},
    )
    assert loc_r.status_code == 201
    location_id = loc_r.json()["id"]
    # Create product
    prod_r = await client.post(
        "/api/v2/products",
        headers=headers,
        json={"name": "Stock Test Product"},
    )
    assert prod_r.status_code == 201
    product_id = prod_r.json()["id"]

    # Add stock
    add_r = await client.post(
        "/api/v2/stock/add",
        headers=headers,
        json={"product_id": product_id, "location_id": location_id, "quantity": 5},
    )
    assert add_r.status_code == 200
    assert add_r.json()["quantity"] == 5

    # List stock
    stock_r = await client.get("/api/v2/stock", headers=headers)
    assert stock_r.status_code == 200
    entries = [e for e in stock_r.json() if e["product_id"] == product_id]
    assert len(entries) == 1
    assert entries[0]["quantity"] == 5
    assert entries[0]["product_name"] == "Stock Test Product"

    # Consume 2
    consume_r = await client.post(
        "/api/v2/stock/consume",
        headers=headers,
        json={"product_id": product_id, "quantity": 2},
    )
    assert consume_r.status_code == 200

    # List stock again
    stock_r2 = await client.get("/api/v2/stock", headers=headers)
    entries2 = [e for e in stock_r2.json() if e["product_id"] == product_id]
    assert len(entries2) == 1
    assert entries2[0]["quantity"] == 3


@pytest.mark.asyncio
@pytest.mark.skipif(SKIP_DB, reason="Requires PostgreSQL with homebot schema")
async def test_product_barcode_add_remove(client, auth_headers, tenant_id):
    """Create product, add barcode, get product has barcode, remove barcode."""
    headers = {**auth_headers, "X-Tenant-ID": tenant_id}
    prod_r = await client.post(
        "/api/v2/products",
        headers=headers,
        json={"name": "Barcode Test Product"},
    )
    assert prod_r.status_code == 201
    product_id = prod_r.json()["id"]
    assert prod_r.json().get("barcodes", []) == []

    add_bc = await client.post(
        f"/api/v2/products/{product_id}/barcodes",
        headers=headers,
        json={"barcode": "1234567890123"},
    )
    assert add_bc.status_code == 201

    get_r = await client.get(f"/api/v2/products/{product_id}", headers=headers)
    assert get_r.status_code == 200
    assert "1234567890123" in get_r.json().get("barcodes", [])

    del_r = await client.delete(
        f"/api/v2/products/{product_id}/barcodes/1234567890123",
        headers=headers,
    )
    assert del_r.status_code == 204

    get_r2 = await client.get(f"/api/v2/products/{product_id}", headers=headers)
    assert "1234567890123" not in get_r2.json().get("barcodes", [])
