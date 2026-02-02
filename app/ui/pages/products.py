"""Products page UI."""

import asyncio
from typing import Any

from nicegui import ui

from app.services.grocy import grocy_client
from app.ui.layout import create_header, create_mobile_nav


def _detail_row(label: str, value: str) -> None:
    """Render a label/value row in the detail popup."""
    with ui.row().classes("w-full gap-2"):
        ui.label(f"{label}:").classes("text-gray-500 w-40 shrink-0")
        ui.label(value or "-").classes("flex-grow break-words")


def _product_picture_url(product: dict[str, Any]) -> str | None:
    """Build Grocy product picture URL if picture_file_name is set."""
    fn = product.get("picture_file_name")
    if not fn:
        return None
    base = grocy_client.api_url.rstrip("/")
    return f"{base}/api/files/productpictures/{fn}"


class ProductsPage:
    """Products page controller."""

    def __init__(self) -> None:
        self._products: list[dict[str, Any]] = []
        self._filtered_products: list[dict[str, Any]] = []
        self._stock_by_product_id: dict[int, float] = {}
        self._location_names: dict[int, str] = {}
        self._unit_names: dict[int, str] = {}
        self._products_container: ui.column | None = None
        self._status_label: ui.label | None = None
        self._search_input: ui.input | None = None
        self._loading = False

    async def load_products(self) -> None:
        """Load products, stock, locations and quantity units from Grocy."""
        if self._loading:
            return

        self._loading = True
        if self._status_label:
            self._status_label.text = "Loading..."
            self._status_label.visible = True

        try:
            products, stock_list, locations, quantity_units = await asyncio.gather(
                grocy_client.get_products(),
                grocy_client.get_stock(),
                grocy_client.get_locations(),
                grocy_client.get_quantity_units(),
            )
            self._products = products
            self._filtered_products = products

            self._stock_by_product_id = {
                int(s["product_id"]): float(s.get("amount", 0) or 0)
                for s in stock_list
                if isinstance(s, dict) and "product_id" in s
            }
            self._location_names = {int(loc["id"]): loc.get("name", "") for loc in (locations or []) if isinstance(loc, dict)}
            self._unit_names = {int(qu["id"]): qu.get("name", "") for qu in (quantity_units or []) if isinstance(qu, dict)}

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
                or search_lower in (p.get("description") or "").lower()
            ]
        self._update_display()

    def _show_product_detail(self, product: dict[str, Any]) -> None:
        """Open a read-only detail popup for the product."""
        pid = product.get("id")
        stock_amount = self._stock_by_product_id.get(pid, 0) if pid is not None else 0
        loc_id = product.get("location_id")
        qu_id = product.get("qu_id_stock") or product.get("qu_id_consume")
        location_name = self._location_names.get(loc_id, str(loc_id) if loc_id is not None else "-")
        unit_name = self._unit_names.get(qu_id, str(qu_id) if qu_id is not None else "-")
        picture_url = _product_picture_url(product)

        with ui.dialog() as dialog:
            with ui.card().classes("w-full max-w-lg"):
                with ui.row().classes("w-full items-center justify-between mb-4"):
                    ui.label("Product details").classes("text-xl font-bold")
                    ui.button(icon="close", on_click=dialog.close).props("flat round dense")

                with ui.row().classes("w-full gap-4 mb-4"):
                    if picture_url:
                        ui.image(picture_url).classes("w-24 h-24 object-cover rounded")
                    else:
                        with ui.element("div").classes(
                            "w-24 h-24 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center"
                        ):
                            ui.icon("inventory_2", size="lg", color="gray")

                    with ui.column().classes("flex-grow gap-1"):
                        ui.label(product.get("name") or "Unknown").classes("text-lg font-semibold")
                        ui.label(f"ID: {product.get('id', '-')}").classes("text-sm text-gray-500")

                with ui.column().classes("w-full gap-2"):
                    _detail_row("Description", (product.get("description") or "-")[:200] or "-")
                    _detail_row("Location", location_name)
                    _detail_row("Quantity in stock", str(stock_amount))
                    _detail_row("Unit", unit_name)
                    _detail_row("Min. stock", str(product.get("min_stock_amount") or 0))
                    if product.get("calories") is not None:
                        _detail_row("Calories", str(product.get("calories")))
                    if product.get("default_best_before_days"):
                        _detail_row("Default best-before (days)", str(product.get("default_best_before_days")))

                ui.button("Close", on_click=dialog.close).props("flat").classes("mt-4")

        dialog.open()

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
                    ui.label("Name").classes("flex-grow min-w-0")
                    ui.label("Description").classes("w-40 hidden md:block shrink-0")
                    ui.label("Location").classes("w-24 hidden lg:block shrink-0")
                    ui.label("Qty").classes("w-14 shrink-0 text-right")
                    ui.label("Min").classes("w-12 shrink-0 text-right hidden lg:block")
                    ui.label("Unit").classes("w-16 hidden xl:block shrink-0")
                    ui.label("ID").classes("w-12 shrink-0 text-right")

                for product in self._filtered_products[:50]:
                    pid = product.get("id")
                    stock_amount = self._stock_by_product_id.get(pid, 0) if pid is not None else 0
                    loc_id = product.get("location_id")
                    qu_id = product.get("qu_id_stock") or product.get("qu_id_consume")
                    location_name = self._location_names.get(loc_id, str(loc_id) if loc_id is not None else "-")
                    unit_name = self._unit_names.get(qu_id, str(qu_id) if qu_id is not None else "-")
                    min_stock = product.get("min_stock_amount") or 0

                    with ui.row().classes(
                        "w-full p-2 border-b hover:bg-gray-50 dark:hover:bg-gray-700 items-center cursor-pointer"
                    ).on("click", lambda p=product: self._show_product_detail(p)):
                        ui.label(product.get("name") or "Unknown").classes("flex-grow min-w-0 truncate")
                        desc = product.get("description") or ""
                        ui.label(desc[:25] + "…" if len(desc) > 25 else (desc or "-")).classes(
                            "w-40 text-gray-500 text-sm hidden md:block truncate shrink-0"
                        )
                        ui.label(location_name).classes("w-24 text-gray-500 text-sm hidden lg:block truncate shrink-0")
                        ui.label(str(int(stock_amount) if stock_amount == int(stock_amount) else stock_amount)).classes(
                            "w-14 text-right shrink-0"
                        )
                        ui.label(str(min_stock)).classes("w-12 text-right text-gray-500 hidden lg:block shrink-0")
                        ui.label(unit_name).classes("w-16 text-gray-500 text-sm hidden xl:block truncate shrink-0")
                        ui.label(str(product.get("id") or "-")).classes("w-12 text-right text-gray-400 text-sm shrink-0")

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
