"""Tests for authentication service."""

from datetime import datetime, timedelta, timezone

import pytest

from app.services.auth import (
    Session,
    SessionStore,
    hash_password,
    verify_password,
)


def test_hash_password() -> None:
    """Test password hashing."""
    password = "secure_password_123"
    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$2b$")  # bcrypt prefix
    assert len(hashed) == 60  # bcrypt hash length


def test_verify_password_correct() -> None:
    """Test password verification with correct password."""
    password = "secure_password_123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_incorrect() -> None:
    """Test password verification with incorrect password."""
    password = "secure_password_123"
    hashed = hash_password(password)

    assert verify_password("wrong_password", hashed) is False


def test_verify_password_invalid_hash() -> None:
    """Test password verification with invalid hash."""
    assert verify_password("password", "invalid_hash") is False


def test_session_is_expired_false() -> None:
    """Test session that is not expired."""
    now = datetime.now(timezone.utc)
    session = Session(
        session_id="test123",
        user_id="user1",
        username="testuser",
        created_at=now,
        last_activity=now,
        expires_at=now + timedelta(days=7),
    )

    assert session.is_expired() is False


def test_session_is_expired_absolute() -> None:
    """Test session expired by absolute timeout."""
    now = datetime.now(timezone.utc)
    session = Session(
        session_id="test123",
        user_id="user1",
        username="testuser",
        created_at=now - timedelta(days=8),
        last_activity=now,
        expires_at=now - timedelta(hours=1),  # Expired
    )

    assert session.is_expired() is True


def test_session_refresh() -> None:
    """Test session activity refresh."""
    old_time = datetime.now(timezone.utc) - timedelta(hours=1)
    session = Session(
        session_id="test123",
        user_id="user1",
        username="testuser",
        created_at=old_time,
        last_activity=old_time,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )

    session.refresh()
    assert session.last_activity > old_time


def test_session_store_create_session() -> None:
    """Test creating a session in the store."""
    store = SessionStore()
    session = store.create_session("user1", "testuser")

    assert session.session_id is not None
    assert session.user_id == "user1"
    assert session.username == "testuser"
    assert len(session.session_id) > 20


def test_session_store_get_session() -> None:
    """Test getting a session from the store."""
    store = SessionStore()
    created = store.create_session("user1", "testuser")

    retrieved = store.get_session(created.session_id)
    assert retrieved is not None
    assert retrieved.user_id == "user1"


def test_session_store_get_session_not_found() -> None:
    """Test getting a non-existent session."""
    store = SessionStore()
    result = store.get_session("nonexistent")

    assert result is None


def test_session_store_delete_session() -> None:
    """Test deleting a session."""
    store = SessionStore()
    session = store.create_session("user1", "testuser")

    assert store.delete_session(session.session_id) is True
    assert store.get_session(session.session_id) is None


def test_session_store_delete_session_not_found() -> None:
    """Test deleting a non-existent session."""
    store = SessionStore()
    assert store.delete_session("nonexistent") is False
