"""Tests for lookup providers."""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.lookup.base import LookupResult
from app.services.lookup.openfoodfacts import OpenFoodFactsProvider


class TestOpenFoodFactsProvider:
    """Tests for OpenFoodFacts provider."""

    @pytest.fixture
    def provider(self) -> OpenFoodFactsProvider:
        """Create provider instance."""
        return OpenFoodFactsProvider()

    def test_provider_name(self, provider: OpenFoodFactsProvider) -> None:
        """Test provider name."""
        assert provider.name == "openfoodfacts"

    @pytest.mark.asyncio
    async def test_lookup_disabled(self) -> None:
        """Test lookup when provider is disabled."""
        provider = OpenFoodFactsProvider()
        provider.enabled = False

        result = await provider.lookup("1234567890123")

        assert result.found is False
        assert result.provider == "openfoodfacts"

    @pytest.mark.asyncio
    async def test_lookup_product_found(self, provider: OpenFoodFactsProvider) -> None:
        """Test successful product lookup."""
        mock_response = {
            "status": 1,
            "product": {
                "product_name": "Test Product",
                "brands": "Test Brand",
                "categories": "Snacks, Chips",
                "image_url": "https://example.com/image.jpg",
            },
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = lambda: None

            result = await provider.lookup("1234567890123")

            assert result.found is True
            assert "Test Product" in result.name
            assert result.brand == "Test Brand"

    @pytest.mark.asyncio
    async def test_lookup_product_not_found(self, provider: OpenFoodFactsProvider) -> None:
        """Test product not found."""
        mock_response = {"status": 0}

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = lambda: None

            result = await provider.lookup("0000000000000")

            assert result.found is False


class TestLookupResult:
    """Tests for LookupResult model."""

    def test_lookup_result_creation(self) -> None:
        """Test creating a lookup result."""
        result = LookupResult(
            barcode="1234567890123",
            found=True,
            provider="test",
            name="Test Product",
        )

        assert result.barcode == "1234567890123"
        assert result.found is True
        assert result.name == "Test Product"

    def test_lookup_result_not_found(self) -> None:
        """Test lookup result for not found."""
        result = LookupResult(
            barcode="0000000000000",
            found=False,
            provider="test",
        )

        assert result.found is False
        assert result.name is None
