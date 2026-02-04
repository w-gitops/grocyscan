"""Integration tests for scan endpoints."""

import pytest
from httpx import AsyncClient


class TestScanEndpoints:
    """Integration tests for scan API endpoints."""

    @pytest.mark.asyncio
    async def test_scan_barcode_valid(self, async_client: AsyncClient) -> None:
        """Test scanning a valid barcode."""
        response = await async_client.post(
            "/api/scan",
            json={
                "barcode": "4006381333931",
                "input_method": "manual",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "scan_id" in data
        assert data["barcode"] == "4006381333931"
        assert data["barcode_type"] == "EAN-13"

    @pytest.mark.asyncio
    async def test_scan_barcode_invalid(self, async_client: AsyncClient) -> None:
        """Test scanning an invalid barcode."""
        response = await async_client.post(
            "/api/scan",
            json={
                "barcode": "invalid",
                "input_method": "manual",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["found"] is False
        assert data["barcode_type"] == "UNKNOWN"

    @pytest.mark.asyncio
    async def test_scan_location_barcode(self, async_client: AsyncClient) -> None:
        """Test scanning a location barcode."""
        response = await async_client.post(
            "/api/scan",
            json={
                "barcode": "LOC-PANTRY-01",
                "input_method": "manual",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["barcode_type"] == "LOCATION"
        assert data["location_code"] == "LOC-PANTRY-01"

    @pytest.mark.asyncio
    async def test_cancel_scan(self, async_client: AsyncClient) -> None:
        """Test cancelling a scan session."""
        # First create a scan
        scan_response = await async_client.post(
            "/api/scan",
            json={"barcode": "4006381333931", "input_method": "manual"},
        )
        scan_id = scan_response.json()["scan_id"]

        # Cancel it
        response = await async_client.delete(f"/api/scan/{scan_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_scan(self, async_client: AsyncClient) -> None:
        """Test cancelling a non-existent scan."""
        response = await async_client.delete("/api/scan/nonexistent-id")
        assert response.status_code == 200
        assert response.json()["status"] == "not_found"
