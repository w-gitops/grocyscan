"""Products page UI."""

import asyncio
from typing import Any

import httpx
from nicegui import ui

from app.services.grocy import grocy_client
from app.ui.layout import create_header, create_mobile_nav

# Session/device API (Phase 3 - Homebot inventory); relative so it works from any host
API_BASE_ME = ""
DEVICE_FINGERPRINT_KEY = "device_fingerprint"
API_COOKIE_KEY = "api_cookie"


def _me_headers() -> dict[str, str]:
    """Headers for /api/me requests (cookie + X-Device-ID from storage)."""
    from nicegui import app
    fp = app.storage.user.get(DEVICE_FINGERPRINT_KEY) or ""
    cookie = app.storage.user.get(API_COOKIE_KEY) or ""
    h: dict[str, str] = {"X-Device-ID": fp}
    if cookie:
        h["Cookie"] = cookie
    return h


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
        # Homebot (Phase 3): source "grocy" | "homebot"
        self._source: str = "grocy"
        self._homebot_products: list[dict[str, Any]] = []
        self._homebot_search_q: str = ""

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
        if self._source == "homebot":
            self._homebot_search_q = search_term or ""
            self._filter_homebot()
            return
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

    def _filter_homebot(self) -> None:
        """Filter homebot products by _homebot_search_q."""
        if not self._homebot_search_q.strip():
            self._filtered_products = self._homebot_products
        else:
            q = self._homebot_search_q.lower()
            self._filtered_products = [
                p for p in self._homebot_products
                if q in (p.get("name") or "").lower()
                or q in (p.get("description") or "").lower()
                or q in (p.get("category") or "").lower()
            ]
        self._update_display()

    async def load_products_homebot(self) -> None:
        """Load homebot products from /api/me/products (session + device)."""
        if self._loading:
            return
        self._loading = True
        if self._status_label:
            self._status_label.text = "Loading Homebot inventory..."
            self._status_label.visible = True
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    f"{API_BASE_ME}/api/me/products",
                    headers=_me_headers(),
                )
                if r.status_code == 401:
                    if self._status_label:
                        self._status_label.text = "Please log in to see Homebot inventory."
                        self._status_label.visible = True
                    self._homebot_products = []
                    return
                if r.status_code == 404 or r.status_code == 400:
                    if self._status_label:
                        self._status_label.text = "Register your device on the Scan page to see Homebot inventory."
                        self._status_label.visible = True
                    self._homebot_products = []
                    return
                if r.status_code != 200:
                    if self._status_label:
                        self._status_label.text = f"Error loading Homebot inventory: {r.status_code}"
                        self._status_label.visible = True
                    self._homebot_products = []
                    return
                data = r.json()
                self._homebot_products = [
                    {
                        "id": str(p["id"]),
                        "name": p.get("name", ""),
                        "description": p.get("description"),
                        "category": p.get("category"),
                    }
                    for p in data
                ]
                self._filter_homebot()
            if self._status_label:
                self._status_label.visible = False
        except Exception as e:
            if self._status_label:
                self._status_label.text = f"Error: {e}"
                self._status_label.visible = True
            self._homebot_products = []
        finally:
            self._loading = False

    async def _show_homebot_product_detail(self, product: dict[str, Any]) -> None:
        """Fetch product detail with stock and open dialog."""
        pid = product.get("id")
        if not pid:
            return
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{API_BASE_ME}/api/me/products/{pid}",
                    headers=_me_headers(),
                )
                if r.status_code != 200:
                    ui.notify("Could not load product detail", type="negative")
                    return
                data = r.json()
        except Exception as e:
            ui.notify(f"Error: {e}", type="negative")
            return
        prod = data.get("product", {})
        stock_list = data.get("stock", [])

        async def _open_edit_form() -> None:
            with ui.dialog() as edit_dialog:
                with ui.card().classes("w-full max-w-md"):
                    ui.label("Edit product").classes("text-lg font-semibold mb-4")
                    name_input = ui.input("Name", value=prod.get("name") or "").classes("w-full")
                    desc_input = ui.input("Description", value=prod.get("description") or "").classes("w-full")
                    cat_input = ui.input("Category", value=prod.get("category") or "").classes("w-full")

                    async def _save_edit() -> None:
                        payload = {
                            "name": name_input.value.strip() or None,
                            "description": desc_input.value.strip() or None,
                            "category": cat_input.value.strip() or None,
                        }
                        payload = {k: v for k, v in payload.items() if v is not None}
                        if not payload:
                            ui.notify("No changes", type="info")
                            return
                        try:
                            async with httpx.AsyncClient(timeout=10) as client:
                                patch_r = await client.patch(
                                    f"{API_BASE_ME}/api/me/products/{pid}",
                                    headers=_me_headers(),
                                    json=payload,
                                )
                                if patch_r.status_code != 200:
                                    ui.notify(f"Update failed: {patch_r.status_code}", type="negative")
                                    return
                                edit_dialog.close()
                                dialog.close()
                                await self.load_products_homebot()
                                self._update_display()
                                ui.notify("Product updated")
                        except Exception as e:
                            ui.notify(f"Error: {e}", type="negative")

                    with ui.row().classes("w-full gap-2 mt-4"):
                        ui.button("Save", on_click=_save_edit).props("color=primary")
                        ui.button("Cancel", on_click=edit_dialog.close).props("flat")
                edit_dialog.open()

        with ui.dialog() as dialog:
            with ui.card().classes("w-full max-w-lg"):
                with ui.row().classes("w-full items-center justify-between mb-4"):
                    ui.label("Product details (Homebot)").classes("text-xl font-bold")
                    ui.button(icon="close", on_click=dialog.close).props("flat round dense")
                with ui.column().classes("w-full gap-2 mb-4"):
                    with ui.row().classes("w-full gap-4"):
                        with ui.element("div").classes(
                            "w-24 h-24 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center"
                        ):
                            ui.icon("inventory_2", size="lg", color="gray")
                        with ui.column().classes("flex-grow gap-1"):
                            ui.label(prod.get("name") or "Unknown").classes("text-lg font-semibold")
                            ui.label(f"ID: {prod.get('id', '-')}").classes("text-sm text-gray-500")
                    _detail_row("Description", (prod.get("description") or "-")[:200] or "-")
                    _detail_row("Category", prod.get("category") or "-")
                    _detail_row("Quantity unit", prod.get("quantity_unit") or "-")
                ui.label("Stock by location").classes("font-semibold mb-2")
                if not stock_list:
                    ui.label("No stock").classes("text-gray-500")
                else:
                    for s in stock_list:
                        with ui.row().classes("w-full gap-2"):
                            ui.label(s.get("location_name", "?")).classes("flex-grow")
                            ui.label(str(s.get("quantity", 0))).classes("shrink-0")
                with ui.row().classes("w-full gap-2 mt-4"):
                    ui.button("Edit", icon="edit", on_click=_open_edit_form).props("flat")
                    ui.button("Close", on_click=dialog.close).props("flat")
        dialog.open()

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
        """Update the products display (Grocy or Homebot)."""
        if not self._products_container:
            return

        self._products_container.clear()
        with self._products_container:
            if self._source == "homebot":
                self._update_display_homebot()
                return
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

    def _update_display_homebot(self) -> None:
        """Render Homebot product list (search-filtered)."""
        if not self._filtered_products:
            if self._homebot_products:
                ui.label("No products match your search").classes("text-gray-500 text-center py-8")
            else:
                ui.label("No Homebot products yet. Add products via Scan.").classes(
                    "text-gray-500 text-center py-8"
                )
            return
        with ui.row().classes("w-full p-2 bg-gray-100 dark:bg-gray-800 font-semibold"):
            ui.label("Name").classes("flex-grow min-w-0")
            ui.label("Description").classes("w-40 hidden md:block shrink-0")
            ui.label("Category").classes("w-28 shrink-0")
        for product in self._filtered_products[:50]:
            with ui.row().classes(
                "w-full p-2 border-b hover:bg-gray-50 dark:hover:bg-gray-700 items-center cursor-pointer"
            ).on("click", lambda p=product: self._show_homebot_product_detail(p)):
                ui.label(product.get("name") or "Unknown").classes("flex-grow min-w-0 truncate")
                desc = product.get("description") or ""
                ui.label(desc[:25] + "…" if len(desc) > 25 else (desc or "-")).classes(
                    "w-40 text-gray-500 text-sm hidden md:block truncate shrink-0"
                )
                ui.label(product.get("category") or "-").classes("w-28 text-gray-500 text-sm truncate shrink-0")
        if len(self._filtered_products) > 50:
            ui.label(f"Showing 50 of {len(self._filtered_products)} products").classes(
                "text-gray-500 text-center py-4"
            )


async def render() -> None:
    """Render the products page."""
    page = ProductsPage()

    async def _set_source(source: str) -> None:
        page._source = source
        if page._search_input:
            page._search_input.value = ""
        if source == "grocy":
            await page.load_products()
        else:
            await page.load_products_homebot()

    async def _refresh() -> None:
        if page._source == "grocy":
            await page.load_products()
        else:
            await page.load_products_homebot()

    create_header()

    with ui.column().classes("w-full max-w-6xl mx-auto p-4"):
        # Page title and actions
        with ui.row().classes("w-full items-center justify-between mb-4"):
            ui.label("Products").classes("text-2xl font-bold")
            with ui.row().classes("gap-2"):
                ui.button("Grocy", on_click=lambda: _set_source("grocy")).props(
                    "color=primary" if page._source == "grocy" else "flat"
                )
                ui.button("Homebot", on_click=lambda: _set_source("homebot")).props(
                    "color=primary" if page._source == "homebot" else "flat"
                )
                ui.button("Refresh", icon="refresh", on_click=_refresh).props("flat")
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