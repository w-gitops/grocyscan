"""Tests for lookup providers."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
    async def test_lookup_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test lookup when provider is disabled."""
        provider = OpenFoodFactsProvider()
        monkeypatch.setattr(
            "app.services.lookup.openfoodfacts._get_settings",
            lambda: SimpleNamespace(openfoodfacts_enabled=False, timeout_seconds=1),
        )

        result = await provider.lookup("1234567890123")

        assert result.found is False
        assert result.provider == "openfoodfacts"

    @pytest.mark.asyncio
    async def test_lookup_product_found(
        self, provider: OpenFoodFactsProvider, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful product lookup."""
        monkeypatch.setattr(
            "app.services.lookup.openfoodfacts._get_settings",
            lambda: SimpleNamespace(openfoodfacts_enabled=True, timeout_seconds=1),
        )
        mock_response = {
            "status": 1,
            "product": {
                "product_name": "Test Product",
                "brands": "Test Brand",
                "categories": "Snacks, Chips",
                "image_url": "https://example.com/image.jpg",
            },
        }

        response = MagicMock()
        response.status_code = 200
        response.json.return_value = mock_response
        response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = response
            result = await provider.lookup("1234567890123")

            assert result.found is True
            assert "Test Product" in result.name
            assert result.brand == "Test Brand"

    @pytest.mark.asyncio
    async def test_lookup_product_not_found(
        self, provider: OpenFoodFactsProvider, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test product not found."""
        monkeypatch.setattr(
            "app.services.lookup.openfoodfacts._get_settings",
            lambda: SimpleNamespace(openfoodfacts_enabled=True, timeout_seconds=1),
        )
        mock_response = {"status": 0}

        response = MagicMock()
        response.status_code = 200
        response.json.return_value = mock_response
        response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = response
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
