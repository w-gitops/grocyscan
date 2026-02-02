"""Integration tests for health endpoints."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    """Test basic health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data


def test_detailed_health_endpoint(client: TestClient) -> None:
    """Test detailed health check endpoint."""
    response = client.get("/api/health/detailed")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert "redis" in data
    assert "grocy" in data
