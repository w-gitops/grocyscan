"""Products page UI."""

from typing import Any

from nicegui import ui

from app.services.grocy import grocy_client
from app.ui.layout import create_header, create_mobile_nav


class ProductsPage:
    """Products page controller."""

    def __init__(self) -> None:
        self._products: list[dict[str, Any]] = []
        self._filtered_products: list[dict[str, Any]] = []
        self._products_container: ui.column | None = None
        self._status_label: ui.label | None = None
        self._search_input: ui.input | None = None
        self._loading = False

    async def load_products(self) -> None:
        """Load products from Grocy."""
        if self._loading:
            return
        
        self._loading = True
        if self._status_label:
            self._status_label.text = "Loading..."
            self._status_label.visible = True
        
        try:
            self._products = await grocy_client.get_products()
            self._filtered_products = self._products
            if self._status_label:
                self._status_label.visible = False
            self._update_display()
        except Exception as e:
            if self._status_label:
                self._status_label.text = f"Error loading products: {e}"
                self._status_label.visible = True
        finally:
            self._loading = False

    def _filter_products(self, search_term: str) -> None:
        """Filter products by search term."""
        if not search_term:
            self._filtered_products = self._products
        else:
            search_lower = search_term.lower()
            self._filtered_products = [
                p for p in self._products
                if search_lower in p.get("name", "").lower()
                or search_lower in p.get("description", "").lower()
            ]
        self._update_display()

    def _update_display(self) -> None:
        """Update the products display."""
        if not self._products_container:
            return
        
        self._products_container.clear()
        with self._products_container:
            if not self._filtered_products:
                if self._products:
                    ui.label("No products match your search").classes("text-gray-500 text-center py-8")
                else:
                    ui.label("No products found in Grocy").classes("text-gray-500 text-center py-8")
            else:
                # Header row
                with ui.row().classes("w-full p-2 bg-gray-100 dark:bg-gray-800 font-semibold"):
                    ui.label("Name").classes("flex-grow")
                    ui.label("Description").classes("w-48 hidden md:block")
                    ui.label("Location").classes("w-32 hidden lg:block")
                    ui.label("ID").classes("w-16 text-right")
                
                # Product rows
                for product in self._filtered_products[:50]:  # Limit to 50 for performance
                    with ui.row().classes("w-full p-2 border-b hover:bg-gray-50 dark:hover:bg-gray-700 items-center"):
                        ui.label(product.get("name") or "Unknown").classes("flex-grow")
                        desc = product.get("description") or ""
                        ui.label(desc[:30] if desc else "-").classes("w-48 text-gray-500 text-sm hidden md:block truncate")
                        ui.label(str(product.get("location_id") or "-")).classes("w-32 text-gray-500 text-sm hidden lg:block")
                        ui.label(str(product.get("id") or "-")).classes("w-16 text-right text-gray-400 text-sm")
                
                if len(self._filtered_products) > 50:
                    ui.label(f"Showing 50 of {len(self._filtered_products)} products").classes(
                        "text-gray-500 text-center py-4"
                    )


async def render() -> None:
    """Render the products page."""
    page = ProductsPage()
    
    create_header()

    with ui.column().classes("w-full max-w-6xl mx-auto p-4"):
        # Page title and actions
        with ui.row().classes("w-full items-center justify-between mb-4"):
            ui.label("Products").classes("text-2xl font-bold")
            with ui.row().classes("gap-2"):
                ui.button("Refresh", icon="refresh", on_click=page.load_products).props("flat")
                ui.button("Add Product", icon="add", on_click=lambda: ui.notify("Scan a barcode to add products")).props("color=primary")

        # Search and filter
        with ui.row().classes("w-full gap-4 mb-4"):
            page._search_input = ui.input(
                placeholder="Search products...",
                on_change=lambda e: page._filter_products(e.value)
            ).props('prepend-icon="search"').classes("flex-grow")

        # Status label
        page._status_label = ui.label("Loading...").classes("text-gray-500 text-center py-4")

        # Products table
        with ui.card().classes("w-full"):
            page._products_container = ui.column().classes("w-full")

    create_mobile_nav()
    
    # Load products on page load
    await page.load_products()
