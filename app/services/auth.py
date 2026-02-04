"""Authentication service with session management."""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel, SecretStr

from app.config import settings
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class Session(BaseModel):
    """User session model."""

    session_id: str
    user_id: str
    username: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime

    def is_expired(self) -> bool:
        """Check if session has expired."""
        now = datetime.now(timezone.utc)
        # Check absolute expiration
        if now >= self.expires_at:
            return True
        # Check idle timeout
        idle_timeout = timedelta(hours=settings.session_timeout_hours)
        if now - self.last_activity >= idle_timeout:
            return True
        return False

    def refresh(self) -> None:
        """Refresh session activity timestamp."""
        self.last_activity = datetime.now(timezone.utc)


class SessionStore:
    """In-memory session store.

    For production, this should be backed by Redis.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create_session(self, user_id: str, username: str) -> Session:
        """Create a new session for a user.

        Args:
            user_id: User ID
            username: Username

        Returns:
            Session: New session object
        """
        session_id = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.session_absolute_timeout_days)

        session = Session(
            session_id=session_id,
            user_id=user_id,
            username=username,
            created_at=now,
            last_activity=now,
            expires_at=expires_at,
        )

        self._sessions[session_id] = session
        logger.info("Session created", user_id=user_id, session_id=session_id[:8])
        return session

    def get_session(self, session_id: str) -> Session | None:
        """Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session if found and valid, None otherwise
        """
        session = self._sessions.get(session_id)
        if session is None:
            return None

        if session.is_expired():
            self.delete_session(session_id)
            return None

        # Refresh activity timestamp
        session.refresh()
        return session

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session ID

        Returns:
            bool: True if session was deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("Session deleted", session_id=session_id[:8])
            return True
        return False

    def cleanup_expired(self) -> int:
        """Remove all expired sessions.

        Returns:
            int: Number of sessions removed
        """
        expired = [
            sid for sid, session in self._sessions.items() if session.is_expired()
        ]
        for sid in expired:
            del self._sessions[sid]
        if expired:
            logger.info("Cleaned up expired sessions", count=len(expired))
        return len(expired)


# Global session store
session_store = SessionStore()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Uses cost factor 12 as recommended for security.

    Args:
        password: Plain text password

    Returns:
        str: Bcrypt hash of the password
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash.

    Args:
        password: Plain text password to verify
        password_hash: Bcrypt hash to verify against

    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def decode_jwt(token: str) -> dict | None:
    """Decode and validate JWT; return payload or None."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
        )
        return payload
    except JWTError:
        return None


def get_auth_password_hash() -> str:
    """Get the effective password hash (settings file overrides env)."""
    try:
        from app.services.settings import settings_service

        auth_settings = settings_service.get_section("auth")
        if getattr(auth_settings, "password_hash", ""):
            return auth_settings.password_hash
    except Exception:
        # Fall back to env-based settings
        pass
    return settings.auth_password_hash.get_secret_value()


def set_auth_password_hash(password_hash: str) -> None:
    """Persist the password hash and update in-memory settings."""
    try:
        from app.services.settings import settings_service

        settings_service.update_section("auth", {"password_hash": password_hash})
    except Exception as exc:
        logger.error("Failed to persist auth password hash", error=str(exc))
        raise RuntimeError("Failed to save password") from exc
    settings.auth_password_hash = SecretStr(password_hash)


def authenticate_user(username: str, password: str) -> Session:
    """Authenticate a user and create a session.

    Args:
        username: Username to authenticate
        password: Password to verify

    Returns:
        Session: New session if authentication successful

    Raises:
        AuthenticationError: If authentication fails
    """
    if not settings.auth_enabled:
        # Auth disabled, create session for default user
        return session_store.create_session(
            user_id="default-user",
            username="admin",
        )

    # Verify username
    if username != settings.auth_username:
        logger.warning("Login attempt with invalid username", username=username)
        raise AuthenticationError("Invalid username or password")

    # Verify password
    stored_hash = get_auth_password_hash()
    if not stored_hash:
        logger.error("No password hash configured")
        raise AuthenticationError("Authentication not configured")

    if not verify_password(password, stored_hash):
        logger.warning("Login attempt with invalid password", username=username)
        raise AuthenticationError("Invalid username or password")

    # Create session
    user_id = str(uuid.uuid4())  # MVP: single user, generate ID
    session = session_store.create_session(user_id=user_id, username=username)
    logger.info("User authenticated", username=username)
    return session


def logout_user(session_id: str) -> bool:
    """Log out a user by deleting their session.

    Args:
        session_id: Session ID to invalidate

    Returns:
        bool: True if session was deleted
    """
    return session_store.delete_session(session_id)


def get_session(session_id: str) -> Session | None:
    """Get and validate a session.

    Args:
        session_id: Session ID

    Returns:
        Session if valid, None otherwise
    """
    return session_store.get_session(session_id)


def generate_password_hash(password: str) -> str:
    """Generate a password hash for configuration.

    Utility function to generate hashes for the AUTH_PASSWORD_HASH setting.

    Args:
        password: Plain text password

    Returns:
        str: Bcrypt hash
    """
    return hash_password(password)
