"""Locations page UI."""

from nicegui import ui

from app.ui.app import create_header, create_mobile_nav


async def render() -> None:
    """Render the locations page."""
    create_header()

    with ui.column().classes("w-full max-w-4xl mx-auto p-4"):
        # Page title and actions
        with ui.row().classes("w-full items-center justify-between mb-4"):
            ui.label("Locations").classes("text-2xl font-bold")
            ui.button("Add Location", icon="add", on_click=lambda: None).props("color=primary")

        # Sync status
        with ui.card().classes("w-full mb-4"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("sync", color="primary")
                ui.label("Grocy Sync:").classes("font-semibold")
                ui.label("Connected").classes("text-green-500")
                ui.button("Sync Now", on_click=lambda: None).props("flat dense")

        # Locations list placeholder
        with ui.card().classes("w-full"):
            ui.label("Locations will be displayed here").classes(
                "text-gray-500 text-center py-8"
            )

    create_mobile_nav()
