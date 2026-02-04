"""Tests for application configuration."""

import tomllib
from pathlib import Path

from app.config import Settings


def _pyproject_version() -> str:
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


def test_default_settings() -> None:
    """Test default settings values."""
    settings = Settings()
    assert settings.grocyscan_version == _pyproject_version()
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
