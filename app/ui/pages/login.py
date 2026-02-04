"""Login page UI."""

from fastapi import Request
from nicegui import ui

from app.config import settings


async def render(request: Request | None = None) -> None:
    """Render the login page. Request optional for reading query params (e.g. ?error=invalid)."""
    # Center the login form
    with ui.column().classes("w-full min-h-screen items-center justify-center"):
        with ui.card().classes("w-96 p-6"):
            ui.label("GrocyScan").classes("text-2xl font-bold text-center w-full mb-4")
            ui.label("Sign in to continue").classes("text-gray-500 text-center w-full mb-6")

            # Error from redirect (form submit returns 302 to /login?error=...)
            error_from_url = ""
            if request:
                err = request.query_params.get("error")
                if err == "invalid":
                    error_from_url = "Invalid username or password"
                elif err == "missing":
                    error_from_url = "Please enter username and password"
            if error_from_url:
                ui.label(error_from_url).classes("text-red-500 text-center w-full mb-2")

            # Username input
            username = ui.input(
                label="Username",
                placeholder="Enter your username",
            ).classes("w-full").props("name=username")

            # Password input
            password = ui.input(
                label="Password",
                placeholder="Enter your password",
                password=True,
                password_toggle_button=True,
            ).classes("w-full mt-4").props("name=password")

            # Error message (for client-side validation)
            error_label = ui.label("").classes("text-red-500 text-center w-full mt-2")
            error_label.visible = False

            async def handle_login() -> None:
                """Handle login: auth disabled -> navigate; else submit form from browser so cookie is set."""
                if not settings.auth_enabled:
                    ui.navigate.to("/scan")
                    return
                if not username.value or not password.value:
                    error_label.text = "Please enter username and password"
                    error_label.visible = True
                    return
                # Submit from browser so Set-Cookie is received (server-side httpx would not set browser cookie)
                await ui.run_javascript(
                    f"""
                    var f = document.createElement("form");
                    f.action = "/api/auth/login";
                    f.method = "POST";
                    var u = document.createElement("input");
                    u.name = "username";
                    u.value = {repr(str(username.value))};
                    var p = document.createElement("input");
                    p.name = "password";
                    p.value = {repr(str(password.value))};
                    f.appendChild(u);
                    f.appendChild(p);
                    document.body.appendChild(f);
                    f.submit();
                    """
                )

            # Login button
            ui.button("Sign In", on_click=handle_login).classes(
                "w-full mt-6"
            ).props("color=primary")

            # Demo mode notice
            if settings.is_development and not settings.auth_enabled:
                ui.label("Auth disabled in development mode").classes(
                    "text-xs text-gray-400 text-center w-full mt-4"
                )
