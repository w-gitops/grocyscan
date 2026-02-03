"""Locations page UI."""

from typing import Any

from nicegui import ui

from app.core.exceptions import GrocyError
from app.services.grocy import grocy_client
from app.ui.layout import create_header, create_mobile_nav


def _detail_row(label: str, value: str) -> None:
    """Render a label/value row in the detail popup."""
    with ui.row().classes("w-full gap-2"):
        ui.label(f"{label}:").classes("text-gray-500 w-32 shrink-0")
        ui.label(value or "—").classes("flex-grow break-words")


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

    def _show_add_location_dialog(self) -> None:
        """Open dialog to add a new location."""
        with ui.dialog() as dialog:
            with ui.card().classes("w-full max-w-md"):
                ui.label("Add Location").classes("text-xl font-bold mb-4")
                name_input = ui.input("Name", placeholder="Location name").classes("w-full")
                name_input.props("outlined")
                desc_input = ui.input("Description", placeholder="Optional").classes("w-full")
                desc_input.props("outlined")
                freezer_check = ui.checkbox("Is freezer", value=False)
                error_label = ui.label("").classes("text-red-500 text-sm")

                async def submit() -> None:
                    name = (name_input.value or "").strip()
                    if not name:
                        error_label.text = "Name is required."
                        return
                    error_label.text = ""
                    try:
                        await grocy_client.create_location(
                            name=name,
                            description=(desc_input.value or "").strip() or None,
                            is_freezer=freezer_check.value,
                        )
                        await self.load_locations()
                        dialog.close()
                        ui.notify("Location added", type="positive")
                    except Exception as e:
                        error_label.text = str(e)

                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=dialog.close).props("flat")
                    ui.button("Add", on_click=submit).props("color=primary")
        dialog.open()

    def _show_location_detail(self, loc: dict[str, Any]) -> None:
        """Open detail popup for a location with view/edit and delete."""
        loc_id = loc.get("id")
        loc_name = loc.get("name") or "Unknown"
        loc_desc = loc.get("description") or ""
        loc_freezer = bool(loc.get("is_freezer"))

        with ui.dialog() as dialog:
            with ui.card().classes("w-full max-w-lg"):
                with ui.row().classes("w-full items-center justify-between mb-4"):
                    ui.label("Location details").classes("text-xl font-bold")
                    ui.button(icon="close", on_click=dialog.close).props("flat round dense")

                # Read-only view container (for toggling with edit form)
                view_container = ui.column().classes("w-full gap-2")
                with view_container:
                    _detail_row("Name", loc_name)
                    _detail_row("Description", loc_desc or "—")
                    _detail_row("ID", str(loc_id) if loc_id is not None else "—")
                    _detail_row("Is freezer", "Yes" if loc_freezer else "No")

                # Edit form container (hidden by default)
                edit_container = ui.column().classes("w-full gap-2")
                with edit_container:
                    edit_name = ui.input("Name", value=loc_name).classes("w-full")
                    edit_name.props("outlined")
                    edit_desc = ui.input("Description", value=loc_desc).classes("w-full")
                    edit_desc.props("outlined")
                    edit_freezer = ui.checkbox("Is freezer", value=loc_freezer)
                    edit_error = ui.label("").classes("text-red-500 text-sm")
                edit_container.set_visibility(False)

                def show_view() -> None:
                    view_container.set_visibility(True)
                    edit_container.set_visibility(False)

                def show_edit() -> None:
                    view_container.set_visibility(False)
                    edit_container.set_visibility(True)
                    edit_name.value = loc_name
                    edit_desc.value = loc_desc
                    edit_freezer.value = loc_freezer
                    edit_error.text = ""

                async def save_edit() -> None:
                    name = (edit_name.value or "").strip()
                    if not name:
                        edit_error.text = "Name is required."
                        return
                    if loc_id is None:
                        return
                    try:
                        await grocy_client.update_location(
                            loc_id,
                            name=name,
                            description=(edit_desc.value or "").strip() or "",
                            is_freezer=edit_freezer.value,
                        )
                        await self.load_locations()
                        # Refresh loc dict from updated list for display
                        updated = next((l for l in self._locations if l.get("id") == loc_id), loc)
                        loc.clear()
                        loc.update(updated)
                        show_view()
                        # Update view labels
                        view_container.clear()
                        with view_container:
                            _detail_row("Name", name)
                            _detail_row("Description", (edit_desc.value or "").strip() or "—")
                            _detail_row("ID", str(loc_id))
                            _detail_row("Is freezer", "Yes" if edit_freezer.value else "No")
                        ui.notify("Location updated", type="positive")
                    except Exception as e:
                        edit_error.text = str(e)

                async def do_delete() -> None:
                    if loc_id is None:
                        return
                    try:
                        await grocy_client.delete_location(loc_id)
                        await self.load_locations()
                        dialog.close()
                        ui.notify("Location deleted", type="positive")
                    except GrocyError as e:
                        ui.notify(f"Cannot delete: {e}", type="negative")
                    except Exception as e:
                        ui.notify(str(e), type="negative")

                def confirm_delete() -> None:
                    with ui.dialog() as confirm_dialog:
                        with ui.card().classes("p-4"):
                            ui.label("Delete this location? This may fail if products use it.")
                            with ui.row().classes("mt-4 gap-2"):
                                ui.button("Cancel", on_click=confirm_dialog.close).props("flat")

                                async def on_confirm_delete() -> None:
                                    await do_delete()
                                    confirm_dialog.close()

                                ui.button("Delete", on_click=on_confirm_delete).props("color=negative")
                    confirm_dialog.open()

                with ui.row().classes("w-full gap-2 mt-4"):
                    ui.button("Close", on_click=dialog.close).props("flat")
                    ui.button("Edit", on_click=show_edit).props("flat")
                    ui.button("Cancel", on_click=show_view).props("flat").bind_visibility_from(
                        edit_container, "visible"
                    )
                    ui.button("Save", on_click=save_edit).props("color=primary").bind_visibility_from(
                        edit_container, "visible"
                    )
                    ui.button("Delete", on_click=confirm_delete).props("flat color=negative")

        dialog.open()

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
                        with ui.card().classes("p-4 cursor-pointer").on(
                            "click", lambda loc=loc: self._show_location_detail(loc)
                        ):
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
            ui.button("Add Location", icon="add", on_click=page._show_add_location_dialog).props("color=primary")

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
