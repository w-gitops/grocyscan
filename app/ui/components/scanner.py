"""Barcode scanner component for NiceGUI."""

import asyncio
import inspect
from typing import Callable, Coroutine, Any, Union

from nicegui import ui


# URL for html5-qrcode library
_HTML5_QRCODE_URL = "https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"


class BarcodeScanner:
    """Barcode scanner component supporting camera and manual input.

    Provides a unified interface for:
    - Manual barcode entry
    - USB/Bluetooth scanner input (keyboard wedge)
    - Camera scanning (via html5-qrcode)
    """

    def __init__(
        self,
        on_scan: Callable[[str], Union[None, Coroutine[Any, Any, None]]],
        auto_focus: bool = True,
        show_camera_button: bool = True,
    ) -> None:
        """Initialize the scanner component.

        Args:
            on_scan: Callback when barcode is scanned/entered (can be sync or async)
            auto_focus: Whether to auto-focus the input field
            show_camera_button: Whether to show camera scan button
        """
        self.on_scan = on_scan
        self.auto_focus = auto_focus
        self.show_camera_button = show_camera_button
        self._input: ui.input | None = None
        self._camera_dialog: ui.dialog | None = None
        self._scanner_container_id = f"barcode-scanner-{id(self)}"

    def render(self) -> None:
        """Render the scanner component."""
        # Listen for barcode scanned events from camera
        ui.on(f"barcode_scanned_{id(self)}", self._handle_camera_scan)

        with ui.row().classes("w-full gap-2 items-end"):
            # Barcode input field
            self._input = ui.input(
                label="Barcode",
                placeholder="Scan or enter barcode...",
                on_change=self._handle_input_change,
            ).classes("flex-grow")

            if self.auto_focus:
                self._input.props("autofocus")

            # Bind Enter key to submit - use async handler
            self._input.on("keydown.enter", self._handle_submit)

            # Camera button
            if self.show_camera_button:
                ui.button(icon="qr_code_scanner", on_click=self._open_camera_dialog).props(
                    "color=primary"
                ).tooltip("Open camera scanner")

            # Submit button - use async handler
            ui.button(icon="search", on_click=self._handle_submit).props(
                "color=primary outline"
            ).tooltip("Look up barcode")

    async def _handle_submit(self, e: Any = None) -> None:
        """Handle barcode submission from events."""
        if self._input and self._input.value:
            barcode = self._input.value.strip()
            if barcode:
                self._input.value = ""
                # Call the callback - await if it's async
                result = self.on_scan(barcode)
                if inspect.iscoroutine(result):
                    await result

    async def _handle_input_change(self, e: dict) -> None:
        """Handle input changes for scanner detection.

        USB/Bluetooth scanners typically send data quickly followed by Enter.
        We detect this pattern to auto-submit.
        """
        pass  # For now, just use Enter key submission

    async def _handle_camera_scan(self, e: Any) -> None:
        """Handle barcode scanned from camera."""
        barcode = e.args.get("barcode", "") if hasattr(e, "args") else ""
        if barcode:
            self._close_camera()
            if self._input:
                self._input.value = barcode
            # Call the callback - await if it's async
            result = self.on_scan(barcode)
            if inspect.iscoroutine(result):
                await result

    def _open_camera_dialog(self) -> None:
        """Open the camera scanner dialog with html5-qrcode."""
        status_id = f"camera-status-{id(self)}"
        torch_btn_id = f"torch-btn-{id(self)}"
        
        with ui.dialog() as self._camera_dialog:
            with ui.card().classes("w-full max-w-lg"):
                ui.label("Camera Scanner").classes("text-xl font-bold mb-4")

                # Container for html5-qrcode scanner - larger for better visibility
                scanner_container = ui.element("div").classes(
                    "w-full rounded overflow-hidden"
                ).style("min-height: 350px;")
                scanner_container._props["id"] = self._scanner_container_id

                # Status message with ID for JavaScript updates
                status_label = ui.label("Loading camera library...").classes(
                    "text-sm text-gray-500 text-center mt-2"
                )
                status_label._props["id"] = status_id

                with ui.row().classes("w-full justify-between gap-2 mt-4"):
                    # Torch/flash toggle button
                    torch_btn = ui.button(icon="flashlight_on", on_click=lambda: None).props(
                        "flat round"
                    ).tooltip("Toggle flash")
                    torch_btn._props["id"] = torch_btn_id
                    torch_btn.style("display: none;")  # Hidden by default, shown if torch available
                    
                    ui.button("Cancel", on_click=self._close_camera).props("flat")

        self._camera_dialog.open()

        # Start the camera scanner after dialog opens
        event_name = f"barcode_scanned_{id(self)}"
        ui.run_javascript(f'''
            (async function() {{
                const statusEl = document.getElementById("{status_id}");
                const updateStatus = (msg) => {{
                    console.log("Camera status:", msg);
                    if (statusEl) statusEl.textContent = msg;
                }};
                
                const containerId = "{self._scanner_container_id}";
                const scriptUrl = "{_HTML5_QRCODE_URL}";
                
                // Function to load script dynamically
                const loadScript = (url) => {{
                    return new Promise((resolve, reject) => {{
                        // Check if already loaded
                        if (typeof Html5Qrcode !== 'undefined') {{
                            resolve();
                            return;
                        }}
                        
                        // Check if script tag exists
                        const existingScript = document.querySelector(`script[src="${{url}}"]`);
                        if (existingScript) {{
                            // Script tag exists, wait for it to load
                            if (existingScript.loaded) {{
                                resolve();
                            }} else {{
                                existingScript.addEventListener('load', resolve);
                                existingScript.addEventListener('error', reject);
                            }}
                            return;
                        }}
                        
                        // Create and add script
                        const script = document.createElement('script');
                        script.src = url;
                        script.onload = () => {{
                            script.loaded = true;
                            resolve();
                        }};
                        script.onerror = () => reject(new Error('Failed to load camera library'));
                        document.head.appendChild(script);
                    }});
                }};
                
                try {{
                    // Load the library first
                    updateStatus("Loading camera library...");
                    await loadScript(scriptUrl);
                    
                    // Wait for dialog to render
                    await new Promise(r => setTimeout(r, 300));
                    
                    const container = document.getElementById(containerId);
                    
                    if (!container) {{
                        updateStatus("Error: Scanner container not found");
                        console.error("Scanner container not found:", containerId);
                        return;
                    }}
                    
                    // Verify library is available
                    if (typeof Html5Qrcode === 'undefined') {{
                        updateStatus("Error: Camera library failed to initialize");
                        console.error("Html5Qrcode not available after loading");
                        return;
                    }}
                    
                    // Check for cameras
                    updateStatus("Requesting camera permission...");
                    
                    const cameras = await Html5Qrcode.getCameras();
                    console.log("Available cameras:", cameras);
                    
                    if (!cameras || cameras.length === 0) {{
                        updateStatus("No cameras found");
                        container.innerHTML = '<div style="padding: 20px; text-align: center; color: #fff;">' + 
                            '<p style="margin-bottom: 10px;">No camera detected</p>' +
                            '<p style="font-size: 12px; color: #aaa;">Please ensure:</p>' +
                            '<ul style="font-size: 11px; color: #aaa; text-align: left; margin: 10px 20px;">' +
                            '<li>Camera permission is granted in browser settings</li>' +
                            '<li>No other app is using the camera</li>' +
                            '<li>Site is accessed via HTTPS (required on iOS)</li>' +
                            '</ul></div>';
                        return;
                    }}
                    
                    updateStatus("Starting camera...");
                    
                    // Configure barcode formats - prioritize UPC/EAN (most common product barcodes)
                    const formatsToSupport = [
                        Html5QrcodeSupportedFormats.UPC_A,
                        Html5QrcodeSupportedFormats.UPC_E,
                        Html5QrcodeSupportedFormats.EAN_13,
                        Html5QrcodeSupportedFormats.EAN_8,
                        Html5QrcodeSupportedFormats.CODE_128,
                        Html5QrcodeSupportedFormats.QR_CODE
                    ];
                    
                    console.log("Supported formats:", formatsToSupport);
                    
                    // Check if native BarcodeDetector API is available
                    const useExperimentalFeatures = typeof BarcodeDetector !== 'undefined';
                    console.log("Native BarcodeDetector available:", useExperimentalFeatures);
                    
                    const html5QrCode = new Html5Qrcode(containerId, {{ 
                        formatsToSupport: formatsToSupport,
                        verbose: true,
                        experimentalFeatures: {{
                            useBarCodeDetectorIfSupported: useExperimentalFeatures
                        }}
                    }});
                    window._html5QrCode = html5QrCode;
                    
                    // Use back camera if available, otherwise first camera
                    let cameraId = cameras[0].id;
                    for (const cam of cameras) {{
                        if (cam.label && cam.label.toLowerCase().includes('back')) {{
                            cameraId = cam.id;
                            break;
                        }}
                    }}
                    
                    console.log("Using camera:", cameraId);
                    
                    // Detect if mobile device
                    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
                    console.log("Is mobile:", isMobile);
                    
                    // Scanner config optimized for barcodes
                    // On mobile: use simpler constraints to let camera auto-adjust
                    const scanConfig = {{
                        fps: isMobile ? 10 : 15,
                        qrbox: function(viewfinderWidth, viewfinderHeight) {{
                            // Scan box sized for UPC barcodes - taller aspect ratio
                            // UPC is roughly 3:2 width:height, so make box accommodate that
                            const width = Math.min(viewfinderWidth * 0.85, 320);
                            const height = Math.min(viewfinderHeight * 0.5, width * 0.6);  // 5:3 ratio (taller)
                            return {{ width: Math.floor(width), height: Math.floor(Math.max(height, 100)) }};
                        }},
                        aspectRatio: isMobile ? 1.333333 : 1.777778,  // 4:3 on mobile, 16:9 on desktop
                        disableFlip: false
                    }};
                    
                    console.log("Starting scan with config:", JSON.stringify({{...scanConfig, qrbox: "dynamic"}}));
                    
                    const onScanSuccess = (decodedText, decodedResult) => {{
                        // Barcode detected - emit event to Python
                        console.log("SUCCESS - Barcode detected:", decodedText, decodedResult);
                        updateStatus("Scanned: " + decodedText);
                        emitEvent("{event_name}", {{ barcode: decodedText }});
                    }};
                    
                    let scanAttempts = 0;
                    const onScanFailure = (errorMessage) => {{
                        scanAttempts++;
                        // Log every 50 attempts to show it's working
                        if (scanAttempts % 50 === 0) {{
                            console.log("Scan attempts:", scanAttempts, "Last:", errorMessage?.substring(0, 50));
                        }}
                    }};
                    
                    // Try with facingMode first (better for mobile), fallback to cameraId
                    try {{
                        await html5QrCode.start(
                            {{ facingMode: "environment" }},
                            scanConfig,
                            onScanSuccess,
                            onScanFailure
                        );
                        console.log("Started with facingMode: environment");
                    }} catch (facingErr) {{
                        console.log("facingMode failed, trying cameraId:", facingErr.message);
                        await html5QrCode.start(
                            cameraId,
                            scanConfig,
                            onScanSuccess,
                            onScanFailure
                        );
                        console.log("Started with cameraId:", cameraId);
                    }}
                    
                    // Try to enable zoom and torch if available
                    const torchBtn = document.getElementById("{torch_btn_id}");
                    let torchEnabled = false;
                    
                    try {{
                        // Get the video track to access advanced features
                        const videoElement = document.querySelector(`#${{containerId}} video`);
                        if (videoElement && videoElement.srcObject) {{
                            const track = videoElement.srcObject.getVideoTracks()[0];
                            const capabilities = track.getCapabilities();
                            const settings = track.getSettings();
                            
                            console.log("Camera capabilities:", capabilities);
                            console.log("Current settings:", settings);
                            
                            // Apply zoom if supported (3x for mobile barcode scanning)
                            if (capabilities.zoom) {{
                                const maxZoom = capabilities.zoom.max;
                                const minZoom = capabilities.zoom.min;
                                // Use 3x zoom or max available, whichever is smaller
                                const targetZoom = Math.min(3.0, maxZoom);
                                console.log("Applying zoom:", targetZoom, "(max:", maxZoom, ")");
                                
                                await track.applyConstraints({{
                                    advanced: [{{ zoom: targetZoom }}]
                                }});
                                updateStatus("Zoomed " + targetZoom.toFixed(1) + "x - Point at barcode");
                            }} else {{
                                console.log("Zoom not supported");
                            }}
                            
                            // Enable torch if available
                            if (capabilities.torch) {{
                                console.log("Torch is supported");
                                
                                // Show the torch button
                                if (torchBtn) {{
                                    torchBtn.style.display = "inline-flex";
                                    torchBtn.onclick = async () => {{
                                        try {{
                                            torchEnabled = !torchEnabled;
                                            await track.applyConstraints({{
                                                advanced: [{{ torch: torchEnabled }}]
                                            }});
                                            console.log("Torch toggled:", torchEnabled);
                                            updateStatus(torchEnabled ? "Flash ON - Point at barcode" : "Point camera at barcode");
                                        }} catch (e) {{
                                            console.log("Torch toggle failed:", e.message);
                                        }}
                                    }};
                                }}
                            }} else {{
                                console.log("Torch not supported on this device");
                            }}
                        }}
                    }} catch (capErr) {{
                        console.log("Could not access camera capabilities:", capErr.message);
                        
                        // Fallback: try html5-qrcode's built-in method
                        try {{
                            const track = html5QrCode.getRunningTrackCameraCapabilities();
                            if (track && track.torchFeature && track.torchFeature().isSupported()) {{
                                if (torchBtn) {{
                                    torchBtn.style.display = "inline-flex";
                                    torchBtn.onclick = async () => {{
                                        torchEnabled = !torchEnabled;
                                        await track.torchFeature().apply(torchEnabled);
                                        updateStatus(torchEnabled ? "Flash ON" : "Point at barcode");
                                    }};
                                }}
                            }}
                        }} catch (e) {{
                            console.log("Fallback torch also failed:", e.message);
                        }}
                    }}
                    
                    updateStatus("Point camera at barcode");
                    
                }} catch (err) {{
                    console.error("Camera error:", err);
                    const errorMsg = err.message || err.toString();
                    updateStatus("Error: " + errorMsg);
                    
                    const container = document.getElementById(containerId);
                    if (container) {{
                        let helpText = '';
                        if (errorMsg.includes('Permission') || errorMsg.includes('NotAllowed')) {{
                            helpText = '<p style="font-size: 11px; margin-top: 10px;">Camera permission was denied. Please allow camera access in your browser settings and try again.</p>';
                        }} else if (errorMsg.includes('NotFound') || errorMsg.includes('DevicesNotFound')) {{
                            helpText = '<p style="font-size: 11px; margin-top: 10px;">No camera found on this device.</p>';
                        }} else if (errorMsg.includes('NotReadable') || errorMsg.includes('TrackStartError')) {{
                            helpText = '<p style="font-size: 11px; margin-top: 10px;">Camera is in use by another application. Please close other apps using the camera.</p>';
                        }} else if (errorMsg.includes('load')) {{
                            helpText = '<p style="font-size: 11px; margin-top: 10px;">Could not load camera library. Check your internet connection.</p>';
                        }} else {{
                            helpText = '<p style="font-size: 11px; margin-top: 10px;">On iOS, camera requires HTTPS. Try accessing via a secure connection.</p>';
                        }}
                        
                        container.innerHTML = '<div style="padding: 20px; text-align: center; color: #fff;">' + 
                            '<p style="color: #f88;">Camera Error</p>' +
                            '<p style="font-size: 12px; margin-top: 10px; color: #aaa;">' + errorMsg + '</p>' +
                            helpText +
                            '</div>';
                    }}
                }}
            }})();
        ''')

    def _close_camera(self) -> None:
        """Close the camera dialog and stop scanning."""
        ui.run_javascript('''
            if (window._html5QrCode) {
                window._html5QrCode.stop().catch(err => console.log("Stop error:", err));
                window._html5QrCode = null;
            }
        ''')
        if self._camera_dialog:
            self._camera_dialog.close()

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
