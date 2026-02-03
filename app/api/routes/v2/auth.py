"""API v2 auth: JWT login and API key support (Phase 1)."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel, Field

from app.config import settings
from app.core.exceptions import AuthenticationError
from app.services.auth import verify_password

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
    stored_hash = settings.auth_password_hash.get_secret_value()
    if not stored_hash or not verify_password(data.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = _create_access_token(subject=data.email)
    return LoginResponse(access_token=token, token_type="bearer")


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
