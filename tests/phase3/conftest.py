"""Phase 3 test fixtures."""

from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for Phase 3 API tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """JWT auth headers for v2 API."""
    from app.services.auth import hash_password

    with patch("app.api.routes.v2.auth.settings") as mock_settings:
        mock_settings.auth_username = "test@test.com"
        mock_settings.auth_password_hash.get_secret_value.return_value = hash_password("secret")
        mock_settings.secret_key = "test-secret"
        r = await client.post(
            "/api/v2/auth/login",
            json={"email": "test@test.com", "password": "secret"},
        )
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
