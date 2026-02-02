"""Authentication endpoints."""

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field

from app.config import settings
from app.core.exceptions import AuthenticationError
from app.services.auth import authenticate_user, logout_user

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request model."""

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=100)


class LoginResponse(BaseModel):
    """Login response model."""

    success: bool
    username: str
    message: str


class LogoutResponse(BaseModel):
    """Logout response model."""

    success: bool
    message: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response) -> LoginResponse:
    """Authenticate user and create session.

    Args:
        request: Login credentials
        response: FastAPI response for setting cookies

    Returns:
        LoginResponse: Login result

    Raises:
        AuthenticationError: If credentials are invalid
    """
    session = authenticate_user(request.username, request.password)

    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session.session_id,
        httponly=True,
        secure=settings.is_production,
        samesite="strict",
        max_age=settings.session_absolute_timeout_days * 24 * 60 * 60,
    )

    return LoginResponse(
        success=True,
        username=session.username,
        message="Login successful",
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(request: Request, response: Response) -> LogoutResponse:
    """End user session.

    Args:
        request: Current request (to get session cookie)
        response: FastAPI response for clearing cookies

    Returns:
        LogoutResponse: Logout confirmation
    """
    session_id = request.cookies.get("session_id")

    if session_id:
        logout_user(session_id)

    # Clear session cookie
    response.delete_cookie("session_id")

    return LogoutResponse(
        success=True,
        message="Logged out successfully",
    )


@router.get("/me")
async def get_current_user(request: Request) -> dict[str, str]:
    """Get current authenticated user info.

    Args:
        request: Current request with user state

    Returns:
        dict: User information
    """
    user_id = getattr(request.state, "user_id", None)
    username = getattr(request.state, "username", None)

    if not user_id:
        raise AuthenticationError("Not authenticated")

    return {
        "user_id": user_id,
        "username": username or "unknown",
    }
