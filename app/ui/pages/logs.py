"""Logs page UI."""

from nicegui import ui

from app.ui.layout import create_header, create_mobile_nav


async def render() -> None:
    """Render the logs page."""
    create_header()

    with ui.column().classes("w-full max-w-6xl mx-auto p-4"):
        # Page title
        ui.label("Application Logs").classes("text-2xl font-bold mb-4")

        # Filters
        with ui.row().classes("w-full gap-4 mb-4"):
            ui.select(
                ["All Levels", "DEBUG", "INFO", "WARNING", "ERROR"],
                value="All Levels",
                label="Level",
            ).classes("w-40")

            ui.input(placeholder="Search logs...", icon="search").classes("flex-grow")

            ui.button("Refresh", icon="refresh", on_click=lambda: None).props("outline")
            ui.button("Copy All", icon="content_copy", on_click=lambda: None).props("outline")

        # Logs viewer placeholder
        with ui.card().classes("w-full"):
            with ui.scroll_area().classes("h-96 font-mono text-sm"):
                ui.label("Log entries will be displayed here").classes(
                    "text-gray-500 text-center py-8"
                )

    create_mobile_nav()
