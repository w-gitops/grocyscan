"""Phase 4 test fixtures."""

import os
from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app

# Skip tests that require DB when PostgreSQL with homebot schema is not configured (e.g. CI without DATABASE_URL)
DATABASE_URL = os.environ.get("DATABASE_URL", "")
SKIP_DB = "postgresql" not in DATABASE_URL or "homebot" not in DATABASE_URL


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for Phase 4 API tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=False,
    ) as client:
        yield client


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> AsyncGenerator[dict[str, str], None]:
    """JWT auth headers for v2 API; patch settings in both auth route and services.auth so encode/decode use same secret."""
    from unittest.mock import MagicMock

    from app.services.auth import hash_password

    mock_settings = MagicMock()
    mock_settings.auth_username = "test@test.com"
    mock_settings.auth_password_hash.get_secret_value.return_value = hash_password("secret")
    mock_settings.secret_key = "test-secret"
    with (
        patch("app.api.routes.v2.auth.settings", mock_settings),
        patch("app.services.auth.settings", mock_settings),
    ):
        r = await client.post(
            "/api/v2/auth/login",
            json={"email": "test@test.com", "password": "secret"},
        )
        assert r.status_code == 200
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
    # Yield from inside patch so decode_jwt (used by get_current_user_v2) sees same secret
    with (
        patch("app.api.routes.v2.auth.settings", mock_settings),
        patch("app.services.auth.settings", mock_settings),
    ):
        yield headers


@pytest.fixture
def tenant_id() -> str:
    """Default tenant ID for Phase 4 (matches seed)."""
    return "00000000-0000-0000-0000-000000000001"
