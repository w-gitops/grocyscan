"""Locations page UI."""

from typing import Any

from nicegui import ui

from app.services.grocy import grocy_client
from app.ui.layout import create_header, create_mobile_nav


class LocationsPage:
    """Locations page controller."""

    def __init__(self) -> None:
        self._locations: list[dict[str, Any]] = []
        self._locations_container: ui.column | None = None
        self._sync_status: ui.label | None = None
        self._loading = False

    async def load_locations(self) -> None:
        """Load locations from Grocy."""
        if self._loading:
            return
        
        self._loading = True
        if self._sync_status:
            self._sync_status.text = "Syncing..."
            self._sync_status.classes(remove="text-green-500 text-red-500", add="text-yellow-500")
        
        try:
            self._locations = await grocy_client.get_locations()
            if self._sync_status:
                self._sync_status.text = f"Connected ({len(self._locations)} locations)"
                self._sync_status.classes(remove="text-yellow-500 text-red-500", add="text-green-500")
            self._update_display()
        except Exception as e:
            if self._sync_status:
                self._sync_status.text = f"Error: {e}"
                self._sync_status.classes(remove="text-yellow-500 text-green-500", add="text-red-500")
        finally:
            self._loading = False

    def _update_display(self) -> None:
        """Update the locations display."""
        if not self._locations_container:
            return
        
        self._locations_container.clear()
        with self._locations_container:
            if not self._locations:
                ui.label("No locations found in Grocy").classes("text-gray-500 text-center py-8")
            else:
                with ui.element("div").classes("grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"):
                    for loc in self._locations:
                        with ui.card().classes("p-4"):
                            with ui.row().classes("items-center gap-2"):
                                icon_name = "ac_unit" if loc.get("is_freezer") else "inventory_2"
                                ui.icon(icon_name, color="primary" if loc.get("is_freezer") else "gray")
                                ui.label(loc.get("name", "Unknown")).classes("font-semibold text-lg")
                            if loc.get("description"):
                                ui.label(loc.get("description")).classes("text-gray-500 text-sm mt-1")
                            with ui.row().classes("mt-2 gap-2"):
                                ui.label(f"ID: {loc.get('id')}").classes("text-xs text-gray-400")
                                if loc.get("is_freezer"):
                                    ui.badge("Freezer", color="blue").classes("text-xs")


async def render() -> None:
    """Render the locations page."""
    page = LocationsPage()
    
    create_header()

    with ui.column().classes("w-full max-w-4xl mx-auto p-4"):
        # Page title and actions
        with ui.row().classes("w-full items-center justify-between mb-4"):
            ui.label("Locations").classes("text-2xl font-bold")
            ui.button("Add Location", icon="add", on_click=lambda: ui.notify("Create locations in Grocy")).props("color=primary")

        # Sync status
        with ui.card().classes("w-full mb-4"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("sync", color="primary")
                ui.label("Grocy Sync:").classes("font-semibold")
                page._sync_status = ui.label("Checking...").classes("text-yellow-500")
                ui.button("Sync Now", on_click=page.load_locations).props("flat dense")

        # Locations list
        with ui.card().classes("w-full"):
            page._locations_container = ui.column().classes("w-full")
            with page._locations_container:
                ui.label("Loading...").classes("text-gray-500 text-center py-8")

    create_mobile_nav()
    
    # Load locations on page load
    await page.load_locations()
