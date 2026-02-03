"""Tests for application configuration."""

from app.config import Settings


def test_default_settings() -> None:
    """Test default settings values."""
    settings = Settings()
    assert settings.grocyscan_version == "0.1.0-alpha"
    assert settings.grocyscan_env == "development"
    assert settings.grocyscan_port == 3334


def test_provider_list() -> None:
    """Test provider list property."""
    settings = Settings(lookup_provider_order="openfoodfacts,goupc")
    assert settings.provider_list == ["openfoodfacts", "goupc"]


def test_is_development() -> None:
    """Test is_development property."""
    settings = Settings(grocyscan_env="development")
    assert settings.is_development is True
    assert settings.is_production is False


def test_is_production() -> None:
    """Test is_production property."""
    settings = Settings(grocyscan_env="production")
    assert settings.is_development is False
    assert settings.is_production is True
