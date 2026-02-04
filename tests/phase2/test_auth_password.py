"""Phase 2 auth password change tests."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.settings import settings_service


@pytest.mark.asyncio
async def test_change_password_requires_auth():
    """POST /api/v2/auth/password requires JWT auth."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.post(
            "/api/v2/auth/password",
            json={"current_password": "secret", "new_password": "newsecret1"},
        )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_change_password_updates_hash(
    client, auth_headers, monkeypatch, tmp_path
):
    """Password change updates stored hash and blocks old password."""
    monkeypatch.setattr(settings_service, "SETTINGS_FILE", str(tmp_path / "settings.json"))
    settings_service._settings = None

    r = await client.post(
        "/api/v2/auth/password",
        headers=auth_headers,
        json={
            "current_password": "secret",
            "new_password": "newsecret1",
            "confirm_password": "newsecret1",
        },
    )
    assert r.status_code == 200

    old_login = await client.post(
        "/api/v2/auth/login",
        json={"email": "test@test.com", "password": "secret"},
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v2/auth/login",
        json={"email": "test@test.com", "password": "newsecret1"},
    )
    assert new_login.status_code == 200
