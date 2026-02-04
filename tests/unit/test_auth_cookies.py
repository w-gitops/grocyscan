"""Tests for session cookie helpers in auth routes."""

from unittest.mock import patch

from fastapi import Response

from app.api.routes import auth as auth_routes
from app.config import Settings


def test_set_session_cookie_uses_configured_attributes() -> None:
    """Session cookie uses configured name, domain, and attributes."""
    settings = Settings(
        session_cookie_name="homebot_session",
        session_cookie_domain="homebot.ssiops.com",
        session_cookie_samesite="none",
        session_cookie_secure=True,
        session_cookie_httponly=True,
    )
    response = Response()
    with patch.object(auth_routes, "settings", settings):
        auth_routes._set_session_cookie(response, "session-123")

    cookie = response.headers.get("set-cookie", "")
    lower = cookie.lower()

    assert cookie.startswith("homebot_session=session-123")
    assert "domain=homebot.ssiops.com" in lower
    assert "samesite=none" in lower
    assert "secure" in lower
    assert "httponly" in lower


def test_clear_session_cookie_uses_configured_name_and_domain() -> None:
    """Clear cookie uses configured name and domain."""
    settings = Settings(
        session_cookie_name="homebot_session",
        session_cookie_domain="homebot.ssiops.com",
    )
    response = Response()
    with patch.object(auth_routes, "settings", settings):
        auth_routes._clear_session_cookie(response)

    cookie = response.headers.get("set-cookie", "")
    lower = cookie.lower()

    assert cookie.startswith("homebot_session=")
    assert "domain=homebot.ssiops.com" in lower
    assert "max-age=0" in lower
