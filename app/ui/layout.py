"""Layout components for GrocyScan UI."""

from nicegui import ui

from app.config import settings


def create_header() -> None:
    """Create the application header with navigation."""
    with ui.header().classes("items-center justify-between bg-primary"):
        with ui.row().classes("items-center gap-2"):
            ui.label("GrocyScan").classes(
                "text-xl font-bold text-white cursor-pointer"
            ).on("click", lambda: ui.navigate.to("/"))
            ui.label(f"v{settings.grocyscan_version}").classes(
                "text-xs text-white opacity-70"
            )

        with ui.row().classes("items-center gap-2"):
            ui.button("Scan", on_click=lambda: ui.navigate.to("/scan")).props("flat color=white")
            ui.button("Products", on_click=lambda: ui.navigate.to("/products")).props("flat color=white")
            ui.button("Locations", on_click=lambda: ui.navigate.to("/locations")).props("flat color=white")
            ui.button("Jobs", on_click=lambda: ui.navigate.to("/jobs")).props("flat color=white")
            ui.button("Logs", on_click=lambda: ui.navigate.to("/logs")).props("flat color=white")
            ui.button("Settings", on_click=lambda: ui.navigate.to("/settings")).props("flat color=white")


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
