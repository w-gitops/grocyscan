"""Scan page UI - main barcode scanning interface."""

import hashlib
from typing import Any

import httpx
from fastapi import Request
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
DEVICE_FINGERPRINT_KEY = "device_fingerprint"
API_COOKIE_KEY = "api_cookie"
ACTION_MODES = ("add", "consume", "transfer")
BASE_URL = None  # Set from settings at runtime


def _base_url() -> str:
    return f"http://127.0.0.1:{settings.grocyscan_port}"


def _device_headers() -> dict[str, str]:
    """Headers for /api/me requests: cookie and X-Device-ID from storage."""
    fp = app.storage.user.get(DEVICE_FINGERPRINT_KEY) or ""
    cookie = app.storage.user.get(API_COOKIE_KEY) or ""
    h = {"X-Device-ID": fp}
    if cookie:
        h["Cookie"] = cookie
    return h


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
        # Phase 3: device and action mode
        self._device: dict[str, Any] | None = None
        self._device_dialog: ui.dialog | None = None
        self._action_mode: str = "add"
        self._action_mode_row: ui.row | None = None
        self._quick_action_container: ui.column | None = None  # +1/-1 after scan
        self._last_scanned_barcode: str | None = None
        self._last_scanned_product_id: str | None = None
        self._last_scanned_name: str | None = None

    def _ensure_fingerprint(self, request: Request) -> str:
        """Generate or load device fingerprint; store in user storage. Return fingerprint."""
        fp = app.storage.user.get(DEVICE_FINGERPRINT_KEY)
        if fp:
            return fp
        raw = (
            (request.headers.get("user-agent") or "")
            + (request.headers.get("accept-language") or "")
            + str(getattr(request.client, "host", ""))
        )
        fp = hashlib.sha256(raw.encode()).hexdigest()[:32]
        app.storage.user[DEVICE_FINGERPRINT_KEY] = fp
        return fp

    def _save_api_cookie(self, request: Request) -> None:
        """Store request cookie for later /api/me calls from callbacks."""
        app.storage.user[API_COOKIE_KEY] = request.headers.get("cookie", "")

    async def _check_device_and_show_register_if_needed(self, request: Request) -> None:
        """Ensure fingerprint and cookie; GET /api/me/device. If 404, show registration dialog."""
        self._ensure_fingerprint(request)
        self._save_api_cookie(request)
        base = _base_url()
        headers = _device_headers()
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{base}/api/me/device", headers=headers)
                if r.status_code == 200:
                    self._device = r.json()
                    raw = (self._device.get("default_action") or "add").lower()
                    self._action_mode = "add" if raw == "add_stock" else (raw if raw in ACTION_MODES else "add")
                    if self._action_mode_row:
                        self._update_action_mode_buttons()
                    return
                if r.status_code == 404:
                    self._show_device_registration_dialog()
                    return
        except Exception:
            pass
        # No device and no 404 (e.g. not logged in): don't block scan page

    def _show_device_registration_dialog(self) -> None:
        """Open dialog to register this device (name, device_type)."""
        with ui.dialog() as self._device_dialog, ui.card().classes("w-full max-w-sm"):
            ui.label("Register this device").classes("text-xl font-bold mb-4")
            name_input = ui.input("Device name", value="My tablet").classes("w-full")
            device_type_select = ui.select(
                {"tablet": "Tablet", "phone": "Phone", "desktop": "Desktop"},
                value="tablet",
                label="Device type",
            ).classes("w-full")
            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Register", on_click=self._on_register_device).props("color=primary")
            # Store refs for callback
            self._device_dialog._name_input = name_input
            self._device_dialog._device_type_select = device_type_select
        self._device_dialog.open()

    async def _on_register_device(self) -> None:
        """POST /api/me/device and close dialog."""
        if not self._device_dialog:
            return
        name = getattr(self._device_dialog, "_name_input", None)
        device_type_el = getattr(self._device_dialog, "_device_type_select", None)
        name_val = name.value.strip() if name else "Device"
        device_type_val = device_type_el.value if device_type_el else "tablet"
        fp = app.storage.user.get(DEVICE_FINGERPRINT_KEY) or ""
        if not fp:
            ui.notify("Cannot register: no fingerprint", type="error")
            return
        base = _base_url()
        headers = _device_headers()
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    f"{base}/api/me/device",
                    headers=headers,
                    json={"name": name_val, "device_type": device_type_val, "fingerprint": fp},
                )
                if r.status_code in (200, 201):
                    self._device = r.json()
                    raw = (self._device.get("default_action") or "add").lower()
                    self._action_mode = "add" if raw == "add_stock" else (raw if raw in ACTION_MODES else "add")
                    if self._device_dialog:
                        self._device_dialog.close()
                    if self._action_mode_row:
                        self._update_action_mode_buttons()
                    ui.notify("Device registered", type="positive")
                else:
                    ui.notify(f"Registration failed: {r.text}", type="error")
        except Exception as e:
            ui.notify(f"Error: {e}", type="error")

    def _update_action_mode_buttons(self) -> None:
        """Refresh action mode button states (rebuild row)."""
        if not self._action_mode_row:
            return
        self._action_mode_row.clear()
        with self._action_mode_row:
            for mode in ACTION_MODES:
                label = {"add": "Add Stock", "consume": "Consume", "transfer": "Transfer"}[mode]
                ui.button(
                    label,
                    on_click=lambda m=mode: self._set_action_mode(m),
                ).props("color=primary" if self._action_mode == mode else "flat")

    async def _set_action_mode(self, mode: str) -> None:
        """Set action mode and persist to device."""
        self._action_mode = mode
        self._update_action_mode_buttons()
        if not self._device:
            return
        base = _base_url()
        headers = _device_headers()
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.patch(
                    f"{base}/api/me/device",
                    headers=headers,
                    json={"default_action": mode},
                )
        except Exception:
            pass

    async def _quick_add_one(self) -> None:
        """POST /api/me/stock/add quantity 1 for last scanned product."""
        if not self._last_scanned_product_id:
            return
        base = _base_url()
        headers = _device_headers()
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    f"{base}/api/me/stock/add",
                    headers=headers,
                    json={"product_id": self._last_scanned_product_id, "quantity": 1},
                )
                if r.status_code == 200:
                    ui.notify("+1 added", type="positive")
                    if self.feedback:
                        self.feedback.show_success("+1 added")
                    self._clear_quick_actions()
                else:
                    ui.notify(r.text or "Add failed", type="error")
        except Exception as e:
            ui.notify(f"Error: {e}", type="error")

    async def _quick_consume_one(self) -> None:
        """POST /api/me/stock/consume quantity 1 for last scanned product."""
        if not self._last_scanned_product_id:
            return
        base = _base_url()
        headers = _device_headers()
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    f"{base}/api/me/stock/consume",
                    headers=headers,
                    json={"product_id": self._last_scanned_product_id, "quantity": 1},
                )
                if r.status_code == 200:
                    ui.notify("-1 consumed", type="positive")
                    if self.feedback:
                        self.feedback.show_success("-1 consumed")
                    self._clear_quick_actions()
                else:
                    ui.notify(r.text or "Consume failed", type="error")
        except Exception as e:
            ui.notify(f"Error: {e}", type="error")

    def _clear_quick_actions(self) -> None:
        """Hide quick action area and clear last scanned state."""
        self._last_scanned_barcode = None
        self._last_scanned_product_id = None
        self._last_scanned_name = None
        if self._quick_action_container:
            self._quick_action_container.clear()
            with self._quick_action_container:
                pass

    def _show_quick_actions(self, product_id: str, name: str) -> None:
        """Show +1 / -1 buttons for scanned product (homebot inventory)."""
        self._last_scanned_product_id = product_id
        self._last_scanned_name = name
        if not self._quick_action_container:
            return
        self._quick_action_container.clear()
        with self._quick_action_container:
            ui.label(f"Quick: {name}").classes("font-semibold mb-2")
            with ui.row().classes("gap-2"):
                ui.button("+1", on_click=self._quick_add_one).props("color=primary outline")
                ui.button("-1", on_click=self._quick_consume_one).props("color=orange outline")

    async def handle_scan(self, barcode: str) -> None:
        """Handle barcode scan from scanner component."""
        if self.feedback:
            self.feedback.reset()
        self._clear_quick_actions()

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

                    # Phase 3: if product is in homebot inventory, show quick +1/-1
                    try:
                        base = _base_url()
                        async with httpx.AsyncClient(timeout=5) as client:
                            r = await client.get(
                                f"{base}/api/me/product-by-barcode/{barcode}",
                                headers=_device_headers(),
                            )
                            if r.status_code == 200:
                                info = r.json()
                                self._show_quick_actions(
                                    info["product_id"],
                                    info.get("name", "Product"),
                                )
                    except Exception:
                        pass

                    # Open review popup
                    if self.review_popup:
                        self.review_popup.open({
                            "scan_id": data.get("scan_id"),
                            "barcode": data.get("barcode"),
                            "name": product.get("name"),
                            "description": product.get("description"),
                            "brand": product.get("brand"),
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
                        "description": form_data.get("description"),
                        "brand": form_data.get("brand"),
                        "category": form_data.get("category"),
                        "quantity": form_data.get("quantity", 1),
                        "location_code": form_data.get("location_code"),
                        "best_before": form_data.get("best_before").isoformat() if form_data.get("best_before") else None,
                        "price": form_data.get("price"),
                        "create_in_grocy": True,
                        "use_llm_enhancement": form_data.get("use_llm_enhancement", True),
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


async def render(request: Request) -> None:
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

        # Phase 3: Action mode (Add Stock | Consume | Transfer)
        with ui.card().classes("w-full mb-4"):
            ui.label("Action mode").classes("font-semibold mb-2")
            page._action_mode_row = ui.row().classes("gap-2")
            page._update_action_mode_buttons()

        # Quick actions after scan (+1/-1 when product in homebot)
        with ui.card().classes("w-full mb-4"):
            ui.label("Quick actions").classes("font-semibold mb-2")
            page._quick_action_container = ui.column().classes("w-full")

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

    async def _on_load_device_check() -> None:
        await page._check_device_and_show_register_if_needed(request)

    ui.timer(0.3, _on_load_device_check, once=True)

    create_mobile_nav()
