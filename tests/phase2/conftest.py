"""Phase 2 test fixtures."""

from collections.abc import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for Phase 2 API tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, monkeypatch) -> dict[str, str]:
    """Get auth headers (JWT) for v2 API."""
    from pydantic import SecretStr

    from app.config import settings as app_settings
    from app.services.auth import hash_password

    monkeypatch.setattr(app_settings, "auth_username", "test@test.com")
    monkeypatch.setattr(app_settings, "auth_password_hash", SecretStr(hash_password("secret")))
    monkeypatch.setattr(app_settings, "secret_key", "test-secret")
    monkeypatch.setattr(app_settings, "auth_enabled", True)

    r = await client.post(
        "/api/v2/auth/login",
        json={"email": "test@test.com", "password": "secret"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
def tenant_id() -> str:
    """Default tenant ID for tests (must exist in DB for integration tests)."""
    return "00000000-0000-0000-0000-000000000001"
