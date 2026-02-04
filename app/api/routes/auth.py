"""Authentication endpoints."""

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse
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


def _set_session_cookie(response: Response, session_id: str) -> None:
    """Set session cookie on response."""
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_id,
        httponly=settings.session_cookie_httponly,
        secure=settings.session_cookie_secure_resolved,
        samesite=settings.session_cookie_samesite,
        max_age=settings.session_absolute_timeout_days * 24 * 60 * 60,
        domain=settings.session_cookie_domain_resolved,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    """Clear session cookie on response."""
    response.delete_cookie(
        settings.session_cookie_name,
        domain=settings.session_cookie_domain_resolved,
        path="/",
    )


@router.post("/login")
async def login(request: Request, response: Response):
    """Authenticate user and create session.

    Accepts JSON (returns LoginResponse) or form (returns 302 redirect to /scan).
    Form POST is used by the browser so Set-Cookie is received by the client.
    """
    is_form = (
        "application/x-www-form-urlencoded" in request.headers.get("content-type", "")
        or "multipart/form-data" in request.headers.get("content-type", "")
    )
    if is_form:
        form = await request.form()
        username = (form.get("username") or "").strip()
        password = (form.get("password") or "")
        if not username or not password:
            return RedirectResponse(url="/login?error=missing", status_code=302)
        try:
            session = authenticate_user(username, password)
        except AuthenticationError:
            return RedirectResponse(url="/login?error=invalid", status_code=302)
        redir = RedirectResponse(url="/scan", status_code=302)
        _set_session_cookie(redir, session.session_id)
        return redir
    # JSON body
    body = await request.json()
    login_req = LoginRequest(**body)
    session = authenticate_user(login_req.username, login_req.password)
    _set_session_cookie(response, session.session_id)
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
    session_id = request.cookies.get(settings.session_cookie_name)

    if session_id:
        logout_user(session_id)

    # Clear session cookie
    _clear_session_cookie(response)

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
