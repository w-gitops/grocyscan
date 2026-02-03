"""Phase 1 API structure tests: FastAPI starts, /docs, logging."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_fastapi_starts():
    """[8] FastAPI app starts without errors; GET /health returns 200."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "healthy"


@pytest.mark.asyncio
async def test_docs_returns_swagger_ui():
    """[9] OpenAPI spec: GET /docs returns Swagger UI."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/docs")
    assert r.status_code == 200
    assert "swagger" in r.text.lower() or "openapi" in r.text.lower()


@pytest.mark.asyncio
async def test_openapi_json_valid():
    """[9] GET openapi URL returns valid OpenAPI spec."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/api/v1/openapi.json")
    assert r.status_code == 200
    data = r.json()
    assert "openapi" in data or "swagger" in data
    assert "paths" in data


@pytest.mark.asyncio
async def test_correlation_id_in_response():
    """[10] Requests logged with correlation ID; response carries X-Request-ID."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/health", headers={"X-Request-ID": "test-correlation-123"})
    assert r.status_code == 200
    assert r.headers.get("x-request-id") == "test-correlation-123"
