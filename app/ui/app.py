"""NiceGUI application entry point."""

from nicegui import app, ui

from app.config import settings
from app.core.logging import get_logger
from app.ui.pages import jobs, locations, login, logs, products, scan, ui_settings

logger = get_logger(__name__)


def configure_nicegui() -> None:
    """Configure and set up the NiceGUI application."""
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


def create_header() -> None:
    """Create the application header with navigation."""
    with ui.header().classes("items-center justify-between"):
        with ui.row().classes("items-center gap-4"):
            ui.label("GrocyScan").classes("text-xl font-bold")

        with ui.row().classes("items-center gap-2"):
            ui.button("Scan", on_click=lambda: ui.navigate.to("/scan")).props("flat")
            ui.button("Products", on_click=lambda: ui.navigate.to("/products")).props("flat")
            ui.button("Locations", on_click=lambda: ui.navigate.to("/locations")).props("flat")
            ui.button("Jobs", on_click=lambda: ui.navigate.to("/jobs")).props("flat")
            ui.button("Logs", on_click=lambda: ui.navigate.to("/logs")).props("flat")
            ui.button("Settings", on_click=lambda: ui.navigate.to("/settings")).props("flat")


def create_footer() -> None:
    """Create the application footer."""
    with ui.footer().classes("items-center justify-center"):
        ui.label(f"GrocyScan v{settings.grocyscan_version}").classes("text-sm opacity-70")


def create_mobile_nav() -> None:
    """Create mobile bottom navigation."""
    with ui.footer().classes("md:hidden fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800"):
        with ui.row().classes("w-full justify-around p-2"):
            ui.button(icon="qr_code_scanner", on_click=lambda: ui.navigate.to("/scan")).props(
                "flat round"
            )
            ui.button(icon="inventory_2", on_click=lambda: ui.navigate.to("/products")).props(
                "flat round"
            )
            ui.button(icon="location_on", on_click=lambda: ui.navigate.to("/locations")).props(
                "flat round"
            )
            ui.button(icon="settings", on_click=lambda: ui.navigate.to("/settings")).props(
                "flat round"
            )
