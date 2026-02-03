# Feature PRD: Scanner Gun Mode

**Version:** 1.0  
**Date:** February 2, 2026  
**Status:** Draft  
**Related User Story:** US-2 (Kiosk Mode)

---

## 1. Overview

This feature adds a dedicated "Scanner Gun Mode" toggle to the scan page that optimizes the interface for continuous USB/Bluetooth barcode scanner gun input. When enabled, the barcode input field maintains persistent focus, allowing rapid sequential scanning without manual interaction.

### 1.1 Problem Statement

Currently, users with USB/Bluetooth barcode scanners (keyboard wedge devices) must:
1. Manually click the barcode input field to focus it
2. Re-focus the field after the review popup closes
3. Re-focus if they accidentally click elsewhere on the page

This friction slows down high-volume scanning workflows, particularly in kiosk or batch-entry scenarios.

### 1.2 Solution

Add a toggle button that activates "Scanner Gun Mode" which:
- Maintains aggressive focus on the barcode input field
- Automatically restores focus after scan submission
- Restores focus after review popup interactions
- Provides clear visual indication of the active mode
- Persists the setting across page refreshes

---

## 2. User Story

| ID | As a... | I want to... | So that... | Acceptance Criteria | Priority |
|----|---------|--------------|------------|---------------------|----------|
| **US-SGM-1** | user | toggle Scanner Gun Mode on the scan page | my USB barcode scanner can continuously input without clicking | Toggle button visible, focus maintained after each scan, visual indicator when active | P0 |

---

## 3. Functional Requirements

| ID | Requirement | Details |
|----|-------------|---------|
| **FR-SGM-1** | Toggle button | Add toggle button with `barcode` Material icon next to camera button |
| **FR-SGM-2** | Visual state | Button shows filled/primary color when active, outlined when inactive |
| **FR-SGM-3** | Input focus on enable | Immediately focus barcode input when mode is enabled |
| **FR-SGM-4** | Focus after submit | Automatically re-focus input after barcode submission clears the field |
| **FR-SGM-5** | Focus after popup | Restore focus to input when review popup closes (confirm or cancel) |
| **FR-SGM-6** | Visual indicator | Add highlighted border/glow to input field when mode is active |
| **FR-SGM-7** | State persistence | Save mode state to localStorage, restore on page load |
| **FR-SGM-8** | Tooltip | Display "Scanner Gun Mode" tooltip on hover |

---

## 4. UI Specification

### 4.1 Button Placement

The Scanner Gun Mode toggle is placed between the camera button and search button:

```
┌─────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Barcode                                                   │  │
│  │ [Scan or enter barcode...                              ]  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  [📷 Camera]  [▣ Scanner Gun Mode]  [🔍 Search]                 │
│                     ^                                           │
│                     └── Toggle button (active state shown)      │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Button States

**Inactive State:**
- Icon: `barcode` (Material Icons)
- Style: Outlined button
- Tooltip: "Enable Scanner Gun Mode"

**Active State:**
- Icon: `barcode` (Material Icons)
- Style: Filled/Primary button
- Tooltip: "Disable Scanner Gun Mode"
- Input field: Ring highlight (`ring-2 ring-primary` or Quasar equivalent)

### 4.3 Active Mode Visual Indicator

When Scanner Gun Mode is active, the input field displays a visual cue:

```
┌─────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Barcode                                    🔫 SCANNER MODE │  │
│  │ ╔═══════════════════════════════════════════════════════╗ │  │
│  │ ║ [Scan or enter barcode...                          ]  ║ │  │
│  │ ╚═══════════════════════════════════════════════════════╝ │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  [📷 Camera]  [▣ Scanner Gun Mode ✓]  [🔍 Search]               │
└─────────────────────────────────────────────────────────────────┘
```

The highlighted border (shown as double lines above) provides immediate visual feedback that Scanner Gun Mode is active and the input is ready to receive scanner input.

---

## 5. Technical Implementation

### 5.1 Component Changes

**File: `app/ui/components/scanner.py`**

```python
class BarcodeScanner:
    def __init__(
        self,
        on_scan: Callable[[str], Union[None, Coroutine[Any, Any, None]]],
        auto_focus: bool = True,
        show_camera_button: bool = True,
    ) -> None:
        # ... existing code ...
        self._scanner_gun_mode: bool = False
        self._scanner_gun_button: ui.button | None = None

    def render(self) -> None:
        # ... existing input and camera button code ...
        
        # Scanner Gun Mode toggle button (new)
        self._scanner_gun_button = ui.button(
            icon="barcode",
            on_click=self._toggle_scanner_gun_mode
        ).props("outline").tooltip("Enable Scanner Gun Mode")
        
        # ... existing search button ...

    async def _toggle_scanner_gun_mode(self) -> None:
        """Toggle Scanner Gun Mode on/off."""
        self._scanner_gun_mode = not self._scanner_gun_mode
        
        if self._scanner_gun_mode:
            # Enable mode
            self._scanner_gun_button.props(remove="outline")
            self._scanner_gun_button.props("color=primary")
            self._scanner_gun_button.tooltip("Disable Scanner Gun Mode")
            self._input.classes(add="ring-2 ring-blue-500")
            await self.focus_input()
            # Persist to localStorage
            await ui.run_javascript(
                'localStorage.setItem("scannerGunMode", "true")'
            )
        else:
            # Disable mode
            self._scanner_gun_button.props("outline")
            self._scanner_gun_button.props(remove="color=primary")
            self._scanner_gun_button.tooltip("Enable Scanner Gun Mode")
            self._input.classes(remove="ring-2 ring-blue-500")
            await ui.run_javascript(
                'localStorage.setItem("scannerGunMode", "false")'
            )

    async def focus_input(self) -> None:
        """Focus the barcode input field."""
        if self._input:
            self._input.run_method("focus")

    async def _handle_submit(self, e: Any = None) -> None:
        """Handle barcode submission from events."""
        if self._input and self._input.value:
            barcode = self._input.value.strip()
            if barcode:
                self._input.value = ""
                result = self.on_scan(barcode)
                if inspect.iscoroutine(result):
                    await result
                # Re-focus if Scanner Gun Mode is active
                if self._scanner_gun_mode:
                    await self.focus_input()

    async def restore_focus_if_gun_mode(self) -> None:
        """Restore focus to input if Scanner Gun Mode is active.
        
        Call this from parent page when popup closes.
        """
        if self._scanner_gun_mode:
            await self.focus_input()
```

### 5.2 Page Integration

**File: `app/ui/pages/scan.py`**

```python
class ScanPage:
    async def handle_confirm(self, form_data: dict) -> None:
        """Handle product confirmation from review popup."""
        # ... existing confirmation logic ...
        
        # Close popup
        self.review_popup.close()
        
        # Restore scanner focus if in gun mode
        await self.scanner.restore_focus_if_gun_mode()

    async def handle_cancel(self) -> None:
        """Handle review popup cancellation."""
        self.review_popup.close()
        
        # Restore scanner focus if in gun mode
        await self.scanner.restore_focus_if_gun_mode()
```

### 5.3 State Persistence

On component mount, check localStorage and restore state:

```python
async def _restore_scanner_gun_mode(self) -> None:
    """Restore Scanner Gun Mode state from localStorage."""
    result = await ui.run_javascript(
        'localStorage.getItem("scannerGunMode")'
    )
    if result == "true":
        await self._toggle_scanner_gun_mode()
```

---

## 6. Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | Toggle button visible next to camera button | Visual inspection |
| 2 | Button changes appearance when toggled | Visual inspection |
| 3 | Input field shows highlight when mode active | Visual inspection |
| 4 | Input receives focus when mode enabled | Type test - characters appear in input |
| 5 | Focus returns to input after scan submitted | Scan barcode, verify cursor in input |
| 6 | Focus returns after popup confirm | Scan, confirm, verify cursor in input |
| 7 | Focus returns after popup cancel | Scan, cancel, verify cursor in input |
| 8 | Mode persists across page refresh | Enable mode, refresh, verify still active |
| 9 | Mode can be disabled | Toggle off, verify normal behavior resumes |

---

## 7. Testing Requirements

### 7.1 Unit Tests

```python
# tests/unit/ui/components/test_scanner.py

async def test_scanner_gun_mode_toggle():
    """Test Scanner Gun Mode can be toggled on and off."""
    # Arrange
    scanner = BarcodeScanner(on_scan=lambda b: None)
    
    # Act - Enable
    await scanner._toggle_scanner_gun_mode()
    
    # Assert
    assert scanner._scanner_gun_mode is True
    
    # Act - Disable
    await scanner._toggle_scanner_gun_mode()
    
    # Assert
    assert scanner._scanner_gun_mode is False

async def test_focus_restored_after_submit_in_gun_mode():
    """Test focus returns to input after submission when in gun mode."""
    # Test implementation with mock focus tracking
    pass
```

### 7.2 Integration Tests

```python
# tests/integration/test_scan_workflow.py

async def test_scanner_gun_mode_workflow():
    """Test complete Scanner Gun Mode workflow."""
    # 1. Navigate to scan page
    # 2. Enable Scanner Gun Mode
    # 3. Verify input has focus
    # 4. Simulate barcode scan
    # 5. Confirm in popup
    # 6. Verify input has focus again
    pass
```

### 7.3 Browser Tests (MCP)

Using cursor-browser-extension MCP tools:
1. Navigate to scan page
2. Click Scanner Gun Mode button
3. Take screenshot showing active state
4. Verify input field has focus indicator

---

## 8. Implementation Notes

### 8.1 Focus Management Considerations

- NiceGUI's `run_method("focus")` may need a small delay after DOM updates
- Consider using `await asyncio.sleep(0.1)` before focus if needed
- Test on both desktop and mobile browsers

### 8.2 Accessibility

- Button should have `aria-pressed` attribute reflecting state
- Input should have `aria-label` updated when in scanner mode
- Visual indicator should not rely solely on color (use border/outline too)

### 8.3 Mobile Considerations

- Scanner Gun Mode is primarily for desktop use with USB scanners
- On mobile, the toggle should still work but may have limited utility
- Consider hiding the button on mobile viewports (optional)

---

## Navigation

- **Back to:** [README](README.md)
- **Related:** [UI Specification](07-ui-specification.md), [User Stories](02-user-stories.md)
