"""NiceGUI application entry point."""

from nicegui import app, ui

from app.core.logging import get_logger

logger = get_logger(__name__)


def configure_nicegui() -> None:
    """Configure and set up the NiceGUI application."""
    # Import pages here to avoid circular imports
    from app.ui.pages import jobs, locations, login, logs, products, scan, ui_settings

    # Configure NiceGUI settings
    ui.dark_mode().auto()

    # Register pages
    @ui.page("/")
    async def index_page() -> None:
        """Redirect to scan page."""
        ui.navigate.to("/scan")

    @ui.page("/login")
    async def login_page() -> None:
        """Login page."""
        await login.render()

    @ui.page("/scan")
    async def scan_page() -> None:
        """Main scanning page."""
        await scan.render()

    @ui.page("/products")
    async def products_page() -> None:
        """Products management page."""
        await products.render()

    @ui.page("/locations")
    async def locations_page() -> None:
        """Locations management page."""
        await locations.render()

    @ui.page("/jobs")
    async def jobs_page() -> None:
        """Job queue page."""
        await jobs.render()

    @ui.page("/logs")
    async def logs_page() -> None:
        """Log viewer page."""
        await logs.render()

    @ui.page("/settings")
    async def settings_page() -> None:
        """Settings page."""
        await ui_settings.render()

    logger.info("NiceGUI routes configured")
