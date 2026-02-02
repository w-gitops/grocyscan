"""Scan page UI - main barcode scanning interface."""

from typing import Any

import httpx
from nicegui import app, ui

from app.config import settings
from app.ui.layout import create_header, create_mobile_nav
from app.ui.components import (
    BarcodeScanner,
    ProductReviewPopup,
    ProductSearch,
    ProductSearchResult,
    ScanFeedback,
)

RECENT_SCANS_STORAGE_KEY = "recent_scans"
RECENT_SCANS_MAX = 10
RECENT_SCANS_DISPLAY = 5


def _recent_scans_from_storage() -> list[dict[str, Any]]:
    """Load recent scans from persistent user storage (survives navigation)."""
    raw = app.storage.user.get(RECENT_SCANS_STORAGE_KEY, [])
    if not isinstance(raw, list):
        return []
    return [x for x in raw if isinstance(x, dict)][:RECENT_SCANS_MAX]


def _recent_scans_to_storage(scans: list[dict[str, Any]]) -> None:
    """Save recent scans to persistent user storage."""
    # Keep only JSON-serializable values for storage
    out = []
    for s in scans[:RECENT_SCANS_MAX]:
        out.append({
            "barcode": s.get("barcode"),
            "name": s.get("name"),
            "quantity": s.get("quantity"),
            "success": s.get("success"),
        })
    app.storage.user[RECENT_SCANS_STORAGE_KEY] = out


class ScanPage:
    """Main scanning page controller."""

    def __init__(self) -> None:
        self.scanner: BarcodeScanner | None = None
        self.feedback: ScanFeedback | None = None
        self.review_popup: ProductReviewPopup | None = None
        self.current_location: str | None = None
        self._location_label: ui.label | None = None
        self._recent_scans: list[dict[str, Any]] = _recent_scans_from_storage()
        self._recent_container: ui.column | None = None
        self._scan_mode: str = "barcode"
        self._search_name_mode: str = "grocy"  # "grocy" or "internet"
        self._mode_container: ui.column | None = None
        self._search_sub_container: ui.column | None = None
        self._product_search: ProductSearch | None = None

    async def handle_scan(self, barcode: str) -> None:
        """Handle barcode scan from scanner component."""
        if self.feedback:
            self.feedback.reset()

        try:
            # Call scan API
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"http://localhost:{settings.grocyscan_port}/api/scan",
                    json={
                        "barcode": barcode,
                        "location_code": self.current_location,
                        "input_method": "manual",
                    },
                )

                if response.status_code != 200:
                    if self.feedback:
                        self.feedback.show_error(f"Scan failed: {response.text}")
                    return

                data = response.json()

                # Check if it's a location barcode
                if data.get("barcode_type") == "LOCATION":
                    self._set_location(data.get("location_code"))
                    if self.feedback:
                        self.feedback.show_success(
                            "Location set", data.get("location_code")
                        )
                    return

                # Product barcode
                if data.get("found"):
                    product = data.get("product", {})
                    if self.feedback:
                        self.feedback.show_success(
                            "Product found",
                            product.get("name", "Unknown product"),
                        )

                    # Open review popup
                    if self.review_popup:
                        self.review_popup.open({
                            "scan_id": data.get("scan_id"),
                            "barcode": data.get("barcode"),
                            "name": product.get("name"),
                            "category": product.get("category"),
                            "image_url": product.get("image_url"),
                            "nutrition": product.get("nutrition"),
                            "lookup_provider": data.get("lookup_provider"),
                            "location_code": self.current_location,
                            "existing_in_grocy": data.get("existing_in_grocy"),
                        })
                else:
                    if self.feedback:
                        self.feedback.show_warning(
                            f"Product not found: {barcode}"
                        )

                    # Still open review popup for manual entry
                    if self.review_popup:
                        self.review_popup.open({
                            "scan_id": data.get("scan_id"),
                            "barcode": data.get("barcode"),
                            "name": "",
                            "location_code": self.current_location,
                        })

        except Exception as e:
            if self.feedback:
                self.feedback.show_error(f"Error: {e}")

    async def handle_confirm(self, form_data: dict[str, Any]) -> None:
        """Handle product confirmation from review popup."""
        try:
            scan_id = form_data.get("scan_id")
            if not scan_id:
                ui.notify("Invalid scan session", type="error")
                return

            # Call confirm API
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"http://localhost:{settings.grocyscan_port}/api/scan/{scan_id}/confirm",
                    json={
                        "name": form_data.get("name"),
                        "category": form_data.get("category"),
                        "quantity": form_data.get("quantity", 1),
                        "location_code": form_data.get("location_code"),
                        "best_before": form_data.get("best_before").isoformat() if form_data.get("best_before") else None,
                        "price": form_data.get("price"),
                        "create_in_grocy": True,
                    },
                )

                data = response.json()

                if data.get("success"):
                    ui.notify(
                        f"Added {form_data.get('quantity', 1)}x {form_data.get('name')}",
                        type="positive",
                    )
                    self._add_recent_scan({
                        "barcode": form_data.get("barcode"),
                        "name": form_data.get("name"),
                        "quantity": form_data.get("quantity", 1),
                        "success": True,
                    })
                    if self.feedback:
                        self.feedback.show_success("Added to inventory")
                    # Restore scanner focus if Scanner Gun Mode is active
                    if self.scanner:
                        await self.scanner.restore_focus_if_gun_mode()
                else:
                    ui.notify(data.get("message", "Failed to add"), type="error")
                    if self.feedback:
                        self.feedback.show_error(data.get("message", "Failed"))

        except Exception as e:
            ui.notify(f"Error: {e}", type="error")
            if self.feedback:
                self.feedback.show_error(f"Error: {e}")

    def _set_location(self, location_code: str | None) -> None:
        """Set the current location."""
        self.current_location = location_code
        if self._location_label:
            self._location_label.text = location_code or "Not set"

    def _add_recent_scan(self, scan: dict[str, Any]) -> None:
        """Add a scan to recent history."""
        self._recent_scans.insert(0, scan)
        self._recent_scans = self._recent_scans[:10]  # Keep last 10
        self._update_recent_display()

    def _set_mode(self, mode: str) -> None:
        """Switch between barcode and search modes."""
        self._scan_mode = mode
        if not self._mode_container:
            return
        self._mode_container.clear()
        with self._mode_container:
            if mode == "barcode":
                self.scanner = BarcodeScanner(on_scan=self.handle_scan)
                self.scanner.render()
                self._product_search = None
                self._search_sub_container = None
            else:
                self.scanner = None
                # Sub-toggle: Search Grocy inventory vs Search internet
                with ui.row().classes("w-full gap-2 mb-3"):
                    ui.button(
                        "Search Grocy inventory",
                        icon="inventory_2",
                        on_click=lambda: self._set_search_name_mode("grocy"),
                    ).props(
                        "color=primary" if self._search_name_mode == "grocy" else "flat"
                    )
                    ui.button(
                        "Search internet (like barcode scan)",
                        icon="public",
                        on_click=lambda: self._set_search_name_mode("internet"),
                    ).props(
                        "color=primary" if self._search_name_mode == "internet" else "flat"
                    )
                self._search_sub_container = ui.column().classes("w-full")
                self._render_product_search()

    def _set_search_name_mode(self, mode: str) -> None:
        """Switch between Grocy inventory and internet search."""
        self._search_name_mode = mode
        if self._search_sub_container:
            self._search_sub_container.clear()
            with self._search_sub_container:
                self._render_product_search()

    def _render_product_search(self) -> None:
        """Render the ProductSearch component with current search_name_mode."""
        if not self._search_sub_container:
            return
        self._product_search = ProductSearch(
            on_select=self._handle_product_select,
            search_mode=self._search_name_mode,
        )
        self._product_search.render()

    async def _handle_product_select(self, product: ProductSearchResult) -> None:
        """Handle product selection from name search - create scan session and open popup."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"http://localhost:{settings.grocyscan_port}/api/scan/by-product",
                    json={
                        "grocy_product_id": product.grocy_product_id,
                        "name": product.name,
                        "category": product.category,
                        "image_url": product.image_url,
                        "location_code": self.current_location,
                    },
                )
                if response.status_code != 200:
                    if self.feedback:
                        self.feedback.show_error(
                            f"Failed to add: {response.text}"
                        )
                    return
                data = response.json()
            scan_id = data.get("scan_id")
            if not scan_id and self.review_popup:
                ui.notify("Invalid response from server", type="error")
                return
            if self.review_popup:
                popup_data = {
                    "scan_id": scan_id,
                    "barcode": getattr(product, "barcode", None),
                    "name": product.name,
                    "category": product.category or "",
                    "image_url": product.image_url,
                    "lookup_provider": product.source,
                    "location_code": self.current_location,
                }
                if getattr(product, "nutrition", None):
                    popup_data["nutrition"] = product.nutrition
                self.review_popup.open(popup_data)
        except Exception as e:
            if self.feedback:
                self.feedback.show_error(f"Error: {e}")
            ui.notify(f"Error: {e}", type="error")

    def _update_recent_display(self) -> None:
        """Update the recent scans display."""
        if self._recent_container:
            self._recent_container.clear()
            with self._recent_container:
                if not self._recent_scans:
                    ui.label("No recent scans").classes("text-gray-500 text-center py-4")
                else:
                    for scan in self._recent_scans[:RECENT_SCANS_DISPLAY]:
                        with ui.row().classes("w-full items-center gap-2 p-2 border-b"):
                            if scan.get("success"):
                                ui.icon("check_circle", color="green")
                            else:
                                ui.icon("error", color="red")
                            ui.label(scan.get("name", scan.get("barcode"))).classes(
                                "flex-grow"
                            )
                            if scan.get("quantity"):
                                ui.label(f"x{scan.get('quantity')}").classes(
                                    "text-gray-500"
                                )


async def render() -> None:
    """Render the scan page."""
    page = ScanPage()

    create_header()

    with ui.column().classes("w-full max-w-4xl mx-auto p-4"):
        # Page title
        ui.label("Barcode Scanner").classes("text-2xl font-bold mb-4")

        # Location display
        with ui.card().classes("w-full mb-4"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("location_on", color="primary")
                ui.label("Current Location:").classes("font-semibold")
                page._location_label = ui.label("Not set").classes("text-gray-500")
                ui.button(
                    icon="edit",
                    on_click=lambda: ui.notify("Scan a location barcode to set"),
                ).props("flat round dense")

        # Mode toggle and scanner/search area
        with ui.card().classes("w-full mb-4"):
            with ui.row().classes("w-full gap-2 mb-4"):
                ui.button(
                    "Scan Barcode",
                    icon="qr_code_scanner",
                    on_click=lambda: page._set_mode("barcode"),
                ).props(
                    "color=primary" if page._scan_mode == "barcode" else "flat"
                )
                ui.button(
                    "Search by Name",
                    icon="search",
                    on_click=lambda: page._set_mode("search"),
                ).props(
                    "color=primary" if page._scan_mode == "search" else "flat"
                )
            page._mode_container = ui.column().classes("w-full")
            page._set_mode("barcode")

        # Feedback area
        with ui.card().classes("w-full mb-4"):
            page.feedback = ScanFeedback()
            page.feedback.render()

        # Recent activity (restored from storage when returning to this page)
        with ui.card().classes("w-full"):
            ui.label("Recent Scans").classes("font-semibold mb-2")
            page._recent_container = ui.column().classes("w-full")
            page._update_recent_display()

    # Review popup
    async def on_popup_closed() -> None:
        """Restore scanner focus when popup closes (e.g. Scanner Gun Mode)."""
        if page.scanner:
            await page.scanner.restore_focus_if_gun_mode()

    page.review_popup = ProductReviewPopup(
        on_confirm=page.handle_confirm,
        on_cancel=on_popup_closed,
    )

    create_mobile_nav()
