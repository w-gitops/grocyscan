"""API v2 auth: JWT login and API key support (Phase 1)."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel, Field

from app.api.deps_v2 import get_current_user_v2
from app.config import settings
from app.services.auth import (
    get_auth_password_hash,
    hash_password,
    set_auth_password_hash,
    verify_password,
)

# JWT config
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request (email + password)."""

    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response with JWT access_token."""

    access_token: str
    token_type: str = "bearer"


class PasswordChangeRequest(BaseModel):
    """Password change request (JWT auth)."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str | None = Field(None, min_length=8)


class PasswordChangeResponse(BaseModel):
    """Password change response."""

    success: bool
    message: str


def _create_access_token(subject: str) -> str:
    """Create JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=ALGORITHM,
    )


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest) -> LoginResponse:
    """Authenticate and return JWT. POST /api/v2/auth/login returns access_token."""
    # Phase 1: single-tenant; use configured auth_username/auth_password_hash
    if data.email != settings.auth_username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    stored_hash = get_auth_password_hash(settings.auth_password_hash.get_secret_value())
    if not stored_hash or not verify_password(data.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = _create_access_token(subject=data.email)
    return LoginResponse(access_token=token, token_type="bearer")


@router.post("/password", response_model=PasswordChangeResponse)
async def change_password(
    data: PasswordChangeRequest,
    principal: str = Depends(get_current_user_v2),
) -> PasswordChangeResponse:
    """Change password (JWT auth only)."""
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication is disabled",
        )
    if principal == "api-key":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password change not allowed for API keys",
        )
    stored_hash = get_auth_password_hash()
    if not stored_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication not configured",
        )
    if not verify_password(data.current_password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    if data.confirm_password is not None and data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password confirmation does not match",
        )
    if verify_password(data.new_password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different",
        )
    new_hash = hash_password(data.new_password)
    set_auth_password_hash(new_hash)
    return PasswordChangeResponse(success=True, message="Password updated")


def decode_jwt(token: str) -> dict | None:
    """Decode and validate JWT; return payload or None."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
        )
        return payload
    except JWTError:
        return None
