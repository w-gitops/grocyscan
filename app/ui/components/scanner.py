"""Barcode scanner component for NiceGUI."""

from typing import Callable

from nicegui import ui


class BarcodeScanner:
    """Barcode scanner component supporting camera and manual input.

    Provides a unified interface for:
    - Manual barcode entry
    - USB/Bluetooth scanner input (keyboard wedge)
    - Camera scanning (via QuaggaJS)
    """

    def __init__(
        self,
        on_scan: Callable[[str], None],
        auto_focus: bool = True,
        show_camera_button: bool = True,
    ) -> None:
        """Initialize the scanner component.

        Args:
            on_scan: Callback when barcode is scanned/entered
            auto_focus: Whether to auto-focus the input field
            show_camera_button: Whether to show camera scan button
        """
        self.on_scan = on_scan
        self.auto_focus = auto_focus
        self.show_camera_button = show_camera_button
        self._input: ui.input | None = None
        self._camera_dialog: ui.dialog | None = None

    def render(self) -> None:
        """Render the scanner component."""
        with ui.row().classes("w-full gap-2 items-end"):
            # Barcode input field
            self._input = ui.input(
                label="Barcode",
                placeholder="Scan or enter barcode...",
                on_change=self._handle_input_change,
            ).classes("flex-grow")

            if self.auto_focus:
                self._input.props("autofocus")

            # Bind Enter key to submit
            self._input.on("keydown.enter", self._handle_submit)

            # Camera button
            if self.show_camera_button:
                ui.button(icon="qr_code_scanner", on_click=self._open_camera_dialog).props(
                    "color=primary"
                ).tooltip("Open camera scanner")

            # Submit button
            ui.button(icon="search", on_click=self._handle_submit).props(
                "color=primary outline"
            ).tooltip("Look up barcode")

    async def _handle_input_change(self, e: dict) -> None:
        """Handle input changes for scanner detection.

        USB/Bluetooth scanners typically send data quickly followed by Enter.
        We detect this pattern to auto-submit.
        """
        pass  # For now, just use Enter key submission

    async def _handle_submit(self, e: dict | None = None) -> None:
        """Handle barcode submission."""
        if self._input and self._input.value:
            barcode = self._input.value.strip()
            if barcode:
                self.on_scan(barcode)
                self._input.value = ""

    def _open_camera_dialog(self) -> None:
        """Open the camera scanner dialog."""
        with ui.dialog() as self._camera_dialog:
            with ui.card().classes("w-full max-w-md"):
                ui.label("Camera Scanner").classes("text-xl font-bold mb-4")

                # Camera preview area
                with ui.element("div").classes(
                    "w-full h-64 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center"
                ):
                    ui.label("Camera preview will appear here").classes("text-gray-500")

                    # Note: Full camera implementation requires QuaggaJS integration
                    # This is a placeholder for the UI structure

                ui.label("Point your camera at a barcode").classes(
                    "text-sm text-gray-500 text-center mt-2"
                )

                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=self._camera_dialog.close).props("flat")

        self._camera_dialog.open()

    def focus(self) -> None:
        """Focus the input field."""
        if self._input:
            self._input.run_method("focus")

    def clear(self) -> None:
        """Clear the input field."""
        if self._input:
            self._input.value = ""


class ScanFeedback:
    """Visual and audio feedback for scan results."""

    def __init__(self) -> None:
        self._container: ui.element | None = None
        self._label: ui.label | None = None
        self._icon: ui.icon | None = None

    def render(self) -> ui.element:
        """Render the feedback component."""
        self._container = ui.element("div").classes(
            "w-full p-4 rounded-lg transition-all duration-300"
        )
        with self._container:
            with ui.row().classes("items-center gap-2"):
                self._icon = ui.icon("info", size="md")
                self._label = ui.label("Ready to scan")

        self._container.classes("bg-gray-100 dark:bg-gray-800")
        return self._container

    def show_success(self, message: str, product_name: str | None = None) -> None:
        """Show success feedback."""
        if self._container and self._label and self._icon:
            self._container.classes(
                remove="bg-gray-100 dark:bg-gray-800 bg-red-100 dark:bg-red-900 bg-yellow-100 dark:bg-yellow-900",
                add="bg-green-100 dark:bg-green-900",
            )
            self._icon._props["name"] = "check_circle"
            self._icon._props["color"] = "green"
            self._label.text = message
            if product_name:
                self._label.text = f"{message}: {product_name}"

            # Play success sound (if enabled)
            # ui.run_javascript("new Audio('/static/sounds/success.mp3').play()")

    def show_error(self, message: str) -> None:
        """Show error feedback."""
        if self._container and self._label and self._icon:
            self._container.classes(
                remove="bg-gray-100 dark:bg-gray-800 bg-green-100 dark:bg-green-900 bg-yellow-100 dark:bg-yellow-900",
                add="bg-red-100 dark:bg-red-900",
            )
            self._icon._props["name"] = "error"
            self._icon._props["color"] = "red"
            self._label.text = message

    def show_warning(self, message: str) -> None:
        """Show warning feedback."""
        if self._container and self._label and self._icon:
            self._container.classes(
                remove="bg-gray-100 dark:bg-gray-800 bg-green-100 dark:bg-green-900 bg-red-100 dark:bg-red-900",
                add="bg-yellow-100 dark:bg-yellow-900",
            )
            self._icon._props["name"] = "warning"
            self._icon._props["color"] = "orange"
            self._label.text = message

    def reset(self) -> None:
        """Reset to default state."""
        if self._container and self._label and self._icon:
            self._container.classes(
                remove="bg-green-100 dark:bg-green-900 bg-red-100 dark:bg-red-900 bg-yellow-100 dark:bg-yellow-900",
                add="bg-gray-100 dark:bg-gray-800",
            )
            self._icon._props["name"] = "info"
            self._icon._props["color"] = None
            self._label.text = "Ready to scan"
