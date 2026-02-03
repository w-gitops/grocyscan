"""Product review popup component."""

import inspect
from datetime import date
from typing import Any, Callable

from nicegui import ui

from app.ui.components.date_picker import TouchDatePicker


class ProductReviewPopup:
    """70% width popup for reviewing and editing product details before adding.

    Displays product information from lookup and allows editing
    before confirming addition to inventory.
    """

    def __init__(
        self,
        on_confirm: Callable[[dict[str, Any]], None],
        on_cancel: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the review popup.

        Args:
            on_confirm: Callback when user confirms with edited data
            on_cancel: Callback when user cancels
        """
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self._dialog: ui.dialog | None = None
        self._product_data: dict[str, Any] = {}

        # Form fields
        self._name_input: ui.input | None = None
        self._category_input: ui.input | None = None
        self._quantity_input: ui.number | None = None
        self._date_picker: TouchDatePicker | None = None
        self._price_input: ui.number | None = None
        self._notes_input: ui.textarea | None = None

    def open(self, product_data: dict[str, Any]) -> None:
        """Open the popup with product data.

        Args:
            product_data: Product information to display/edit
        """
        self._product_data = product_data
        self._render()
        if self._dialog:
            self._dialog.open()

    def close(self) -> None:
        """Close the popup."""
        if self._dialog:
            self._dialog.close()

    def _render(self) -> None:
        """Render the popup dialog."""
        with ui.dialog() as self._dialog:
            # Check for touch device - use getattr for compatibility with different NiceGUI versions
            try:
                is_touch = getattr(ui.context.client, 'has_touch', False)
            except Exception:
                is_touch = False
            self._dialog.props("maximized" if is_touch else "")

            with ui.card().classes("w-full max-w-3xl mx-auto"):
                # Header
                with ui.row().classes("w-full items-center justify-between mb-4"):
                    ui.label("Review Product").classes("text-xl font-bold")
                    ui.button(icon="close", on_click=self._handle_cancel).props(
                        "flat round dense"
                    )

                # Product image and basic info
                with ui.row().classes("w-full gap-4 mb-4"):
                    # Image
                    image_url = self._product_data.get("image_url")
                    if image_url:
                        ui.image(image_url).classes("w-32 h-32 object-cover rounded")
                    else:
                        with ui.element("div").classes(
                            "w-32 h-32 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center"
                        ):
                            ui.icon("inventory_2", size="xl", color="gray")

                    # Basic info
                    with ui.column().classes("flex-grow"):
                        barcode = self._product_data.get("barcode", "Unknown")
                        ui.label(f"Barcode: {barcode}").classes("text-gray-500")

                        lookup_provider = self._product_data.get("lookup_provider")
                        if lookup_provider:
                            ui.label(f"Source: {lookup_provider}").classes(
                                "text-sm text-gray-400"
                            )

                # Editable form
                with ui.column().classes("w-full gap-4"):
                    # Name (required)
                    self._name_input = ui.input(
                        label="Product Name *",
                        value=self._product_data.get("name", ""),
                    ).classes("w-full")

                    # Category
                    self._category_input = ui.input(
                        label="Category",
                        value=self._product_data.get("category", ""),
                    ).classes("w-full")

                    # Quantity
                    with ui.row().classes("w-full gap-4"):
                        self._quantity_input = ui.number(
                            label="Quantity",
                            value=1,
                            min=1,
                            max=10000,
                        ).classes("flex-grow")

                        # Location (if set)
                        location = self._product_data.get("location_code")
                        if location:
                            with ui.column():
                                ui.label("Location").classes("text-sm text-gray-500")
                                ui.label(location).classes("font-semibold")

                    # Best before date
                    self._date_picker = TouchDatePicker(
                        label="Best Before Date",
                        initial_value=self._product_data.get("best_before"),
                    )
                    self._date_picker.render()

                    # Price (optional)
                    self._price_input = ui.number(
                        label="Price (optional)",
                        value=None,
                        format="%.2f",
                    ).classes("w-full")

                    # Notes (optional)
                    self._notes_input = ui.textarea(
                        label="Notes (optional)",
                        value="",
                    ).classes("w-full")

                # Nutrition info (if available, read-only)
                nutrition = self._product_data.get("nutrition")
                if nutrition:
                    with ui.expansion("Nutrition Information", icon="restaurant").classes(
                        "w-full"
                    ):
                        with ui.grid(columns=2).classes("gap-2"):
                            for key, value in nutrition.items():
                                if value is not None:
                                    ui.label(f"{key.replace('_', ' ').title()}:")
                                    ui.label(str(value))

                # Action buttons
                with ui.row().classes("w-full justify-end gap-2 mt-6"):
                    ui.button("Cancel", on_click=self._handle_cancel).props("flat")
                    ui.button("Add to Inventory", on_click=self._handle_confirm).props(
                        "color=primary"
                    )

    async def _handle_confirm(self) -> None:
        """Handle confirm button click."""
        if not self._name_input or not self._name_input.value:
            ui.notify("Product name is required", type="warning")
            return

        # Gather form data
        form_data = {
            "name": self._name_input.value,
            "category": self._category_input.value if self._category_input else None,
            "quantity": int(self._quantity_input.value) if self._quantity_input else 1,
            "best_before": self._date_picker.value if self._date_picker else None,
            "price": float(self._price_input.value) if self._price_input and self._price_input.value else None,
            "notes": self._notes_input.value if self._notes_input else None,
            "barcode": self._product_data.get("barcode"),
            "scan_id": self._product_data.get("scan_id"),
        }

        self.close()
        # Handle both sync and async callbacks
        result = self.on_confirm(form_data)
        if inspect.iscoroutine(result):
            await result

    def _handle_cancel(self) -> None:
        """Handle cancel button click."""
        self.close()
        if self.on_cancel:
            self.on_cancel()
