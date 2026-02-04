"""Tests for application configuration."""

import tomllib
from pathlib import Path

import pytest
from pydantic import ValidationError
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


def test_session_cookie_domain_normalizes_url() -> None:
    """Session cookie domain strips scheme and returns hostname."""
    settings = Settings(session_cookie_domain="https://homebot.ssiops.com")
    assert settings.session_cookie_domain == "homebot.ssiops.com"
    assert settings.session_cookie_domain_resolved == "homebot.ssiops.com"


def test_session_cookie_domain_empty_resolves_none() -> None:
    """Blank cookie domain resolves to None."""
    settings = Settings(session_cookie_domain="  ")
    assert settings.session_cookie_domain_resolved is None


def test_session_cookie_samesite_normalized() -> None:
    """Cookie SameSite is normalized to lowercase."""
    settings = Settings(session_cookie_samesite="None")
    assert settings.session_cookie_samesite == "none"


def test_session_cookie_secure_resolved_defaults_to_env() -> None:
    """Secure flag defaults to production-only when unset."""
    prod = Settings(grocyscan_env="production", session_cookie_secure=None)
    dev = Settings(grocyscan_env="development", session_cookie_secure=None)
    assert prod.session_cookie_secure_resolved is True
    assert dev.session_cookie_secure_resolved is False


def test_session_cookie_secure_override() -> None:
    """Secure flag honors explicit override."""
    settings = Settings(grocyscan_env="production", session_cookie_secure=False)
    assert settings.session_cookie_secure_resolved is False


def test_session_cookie_name_required() -> None:
    """Cookie name cannot be empty."""
    with pytest.raises(ValidationError):
        Settings(session_cookie_name="  ")
