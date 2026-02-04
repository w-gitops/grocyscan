"""Integration tests for health endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient) -> None:
    """Test basic health check endpoint."""
    response = await async_client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_detailed_health_endpoint(async_client: AsyncClient) -> None:
    """Test detailed health check endpoint."""
    response = await async_client.get("/api/health/detailed")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert "redis" in data
    assert "grocy" in data
