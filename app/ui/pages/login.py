"""Login page UI."""

from nicegui import ui

from app.config import settings


async def render() -> None:
    """Render the login page."""
    # Center the login form
    with ui.column().classes("w-full min-h-screen items-center justify-center"):
        with ui.card().classes("w-96 p-6"):
            ui.label("GrocyScan").classes("text-2xl font-bold text-center w-full mb-4")
            ui.label("Sign in to continue").classes("text-gray-500 text-center w-full mb-6")

            # Username input
            username = ui.input(
                label="Username",
                placeholder="Enter your username",
            ).classes("w-full")

            # Password input
            password = ui.input(
                label="Password",
                placeholder="Enter your password",
                password=True,
                password_toggle_button=True,
            ).classes("w-full mt-4")

            # Error message
            error_label = ui.label("").classes("text-red-500 text-center w-full mt-2")
            error_label.visible = False

            async def handle_login() -> None:
                """Handle login form submission."""
                if not settings.auth_enabled:
                    ui.navigate.to("/scan")
                    return

                if not username.value or not password.value:
                    error_label.text = "Please enter username and password"
                    error_label.visible = True
                    return

                # Call login API
                try:
                    from httpx import AsyncClient

                    async with AsyncClient() as client:
                        response = await client.post(
                            f"http://localhost:{settings.grocyscan_port}/api/auth/login",
                            json={
                                "username": username.value,
                                "password": password.value,
                            },
                        )

                        if response.status_code == 200:
                            ui.navigate.to("/scan")
                        else:
                            data = response.json()
                            error_label.text = data.get("message", "Login failed")
                            error_label.visible = True
                except Exception as e:
                    error_label.text = f"Connection error: {e}"
                    error_label.visible = True

            # Login button
            ui.button("Sign In", on_click=handle_login).classes(
                "w-full mt-6"
            ).props("color=primary")

            # Demo mode notice
            if settings.is_development and not settings.auth_enabled:
                ui.label("Auth disabled in development mode").classes(
                    "text-xs text-gray-400 text-center w-full mt-4"
                )
