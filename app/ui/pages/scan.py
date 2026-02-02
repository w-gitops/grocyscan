"""Scan page UI - main barcode scanning interface."""

from typing import Any

import httpx
from nicegui import ui

from app.config import settings
from app.ui.layout import create_header, create_mobile_nav
from app.ui.components import BarcodeScanner, ProductReviewPopup, ScanFeedback


class ScanPage:
    """Main scanning page controller."""

    def __init__(self) -> None:
        self.scanner: BarcodeScanner | None = None
        self.feedback: ScanFeedback | None = None
        self.review_popup: ProductReviewPopup | None = None
        self.current_location: str | None = None
        self._location_label: ui.label | None = None
        self._recent_scans: list[dict[str, Any]] = []
        self._recent_container: ui.column | None = None

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

    def _update_recent_display(self) -> None:
        """Update the recent scans display."""
        if self._recent_container:
            self._recent_container.clear()
            with self._recent_container:
                if not self._recent_scans:
                    ui.label("No recent scans").classes("text-gray-500 text-center py-4")
                else:
                    for scan in self._recent_scans[:5]:
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

        # Scanner input area
        with ui.card().classes("w-full mb-4"):
            ui.label("Scan or Enter Barcode").classes("font-semibold mb-2")
            page.scanner = BarcodeScanner(
                on_scan=lambda b: ui.run_background(page.handle_scan(b)),
            )
            page.scanner.render()

        # Feedback area
        with ui.card().classes("w-full mb-4"):
            page.feedback = ScanFeedback()
            page.feedback.render()

        # Recent activity
        with ui.card().classes("w-full"):
            ui.label("Recent Scans").classes("font-semibold mb-2")
            page._recent_container = ui.column().classes("w-full")
            with page._recent_container:
                ui.label("No recent scans").classes("text-gray-500 text-center py-4")

    # Review popup
    page.review_popup = ProductReviewPopup(
        on_confirm=lambda d: ui.run_background(page.handle_confirm(d)),
    )

    create_mobile_nav()
