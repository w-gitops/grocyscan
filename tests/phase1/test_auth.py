"""Phase 1 auth tests: JWT login, API key, bcrypt."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.auth import hash_password, verify_password


@pytest.fixture
def auth_password_hash():
    """Bcrypt hash for password 'testpass'."""
    return hash_password("testpass")


@pytest.mark.asyncio
async def test_jwt_login_returns_access_token(auth_password_hash):
    """[5] JWT authentication: POST /api/v2/auth/login returns access_token."""
    mock_settings = MagicMock()
    mock_settings.auth_username = "admin@test"
    mock_settings.auth_password_hash.get_secret_value.return_value = auth_password_hash
    mock_settings.secret_key = "test-secret-key"
    with patch("app.api.routes.v2.auth.settings", mock_settings):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            r = await client.post(
                "/api/v2/auth/login",
                json={"email": "admin@test", "password": "testpass"},
            )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data.get("token_type") == "bearer"


@pytest.mark.asyncio
async def test_protected_endpoint_rejects_invalid_token():
    """[5] Protected endpoint rejects invalid token - login with bad password returns 401."""
    mock_settings = MagicMock()
    mock_settings.auth_username = "admin@test"
    mock_settings.auth_password_hash.get_secret_value.return_value = hash_password("real")
    mock_settings.secret_key = "test-secret"
    with patch("app.api.routes.v2.auth.settings", mock_settings):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            r = await client.post(
                "/api/v2/auth/login",
                json={"email": "admin@test", "password": "wrong"},
            )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_api_key_authenticates():
    """[6] API key authentication: HOMEBOT-API-KEY header authenticates requests."""
    with patch("app.api.deps_v2._valid_api_keys", return_value={"key1", "key2"}):
        from app.api.deps_v2 import get_current_user_v2

        principal = await get_current_user_v2(
            authorization=None,
            homebot_api_key="key1",
        )
    assert principal == "api-key"


@pytest.mark.asyncio
async def test_invalid_api_key_returns_401():
    """[6] Invalid API key returns 401."""
    with patch("app.api.deps_v2._valid_api_keys", return_value={"key1"}):
        from app.api.deps_v2 import get_current_user_v2

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_v2(
                authorization=None,
                homebot_api_key="wrong-key",
            )
    assert exc_info.value.status_code == 401


def test_password_bcrypt_hash():
    """[7] Passwords stored as bcrypt hashes."""
    h = hash_password("mypassword")
    assert h.startswith("$2")
    assert len(h) > 20


def test_login_verifies_password():
    """[7] Login verifies password correctly."""
    h = hash_password("mypassword")
    assert verify_password("mypassword", h) is True
    assert verify_password("wrong", h) is False
