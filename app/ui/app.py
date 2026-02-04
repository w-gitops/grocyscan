"""NiceGUI application entry point."""

from fastapi import Request
from nicegui import app, ui

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _require_auth(request: Request) -> bool:
    """Return True if request is authenticated or auth disabled; else redirect to login and return False."""
    if not settings.auth_enabled:
        return True
    if getattr(request.state, "user_id", None):
        return True
    ui.navigate.to("/login")
    return False


def configure_nicegui() -> None:
    """Configure and set up the NiceGUI application."""
    # Import pages here to avoid circular imports
    from app.ui.pages import jobs, locations, login, logs, products, scan, ui_settings

    # Configure NiceGUI settings
    ui.dark_mode().auto()

    # Register pages
    @ui.page("/")
    async def index_page(request: Request) -> None:
        """Redirect: unauthenticated -> login, else -> scan. Inject PWA manifest link."""
        ui.add_head_html('<link rel="manifest" href="/manifest.json">')
        ui.add_head_html(
            '<meta name="theme-color" content="#1976d2">'
        )
        async def _register_sw() -> None:
            await ui.run_javascript(
                "if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(()=>{});"
            )

        ui.timer(0.2, _register_sw, once=True)
        if settings.auth_enabled and not getattr(request.state, "user_id", None):
            ui.navigate.to("/login")
            return
        ui.navigate.to("/scan")

    @ui.page("/login")
    async def login_page(request: Request) -> None:
        """Login page."""
        await login.render(request)

    @ui.page("/scan")
    async def scan_page(request: Request) -> None:
        """Main scanning page."""
        if not _require_auth(request):
            return
        await scan.render(request)

    @ui.page("/products")
    async def products_page(request: Request) -> None:
        """Products management page."""
        if not _require_auth(request):
            return
        await products.render()

    @ui.page("/locations")
    async def locations_page(request: Request) -> None:
        """Locations management page."""
        if not _require_auth(request):
            return
        await locations.render()

    @ui.page("/jobs")
    async def jobs_page(request: Request) -> None:
        """Job queue page."""
        if not _require_auth(request):
            return
        await jobs.render()

    @ui.page("/logs")
    async def logs_page(request: Request) -> None:
        """Log viewer page."""
        if not _require_auth(request):
            return
        await logs.render(request)

    @ui.page("/settings")
    async def settings_page(request: Request) -> None:
        """Settings page."""
        if not _require_auth(request):
            return
        await ui_settings.render(request)

    logger.info("NiceGUI routes configured")
