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

**File: `frontend/src/components/BarcodeScanner.vue`**

```vue
<template>
  <div class="barcode-scanner">
    <q-input
      ref="barcodeInput"
      v-model="barcode"
      label="Barcode"
      placeholder="Scan or enter barcode..."
      :class="{ 'scanner-gun-active': scannerGunMode }"
      @keyup.enter="handleSubmit"
      clearable
    >
      <template v-slot:prepend>
        <q-icon name="qr_code" />
      </template>
    </q-input>

    <div class="row q-gutter-sm q-mt-md">
      <q-btn icon="photo_camera" label="Camera" @click="toggleCamera" />
      
      <!-- Scanner Gun Mode toggle button -->
      <q-btn
        :icon="scannerGunMode ? 'barcode' : 'barcode'"
        :color="scannerGunMode ? 'primary' : undefined"
        :outline="!scannerGunMode"
        @click="toggleScannerGunMode"
      >
        <q-tooltip>{{ scannerGunMode ? 'Disable' : 'Enable' }} Scanner Gun Mode</q-tooltip>
      </q-btn>
      
      <q-btn icon="search" label="Search" @click="$emit('search')" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'

const emit = defineEmits(['scan', 'search'])

const barcodeInput = ref(null)
const barcode = ref('')
const scannerGunMode = ref(false)

const toggleScannerGunMode = () => {
  scannerGunMode.value = !scannerGunMode.value
  localStorage.setItem('scannerGunMode', scannerGunMode.value)
  if (scannerGunMode.value) {
    focusInput()
  }
}

const focusInput = () => {
  barcodeInput.value?.focus()
}

const handleSubmit = () => {
  if (barcode.value.trim()) {
    emit('scan', barcode.value.trim())
    barcode.value = ''
    if (scannerGunMode.value) {
      focusInput()
    }
  }
}

// Restore state from localStorage
onMounted(() => {
  scannerGunMode.value = localStorage.getItem('scannerGunMode') === 'true'
  if (scannerGunMode.value) {
    focusInput()
  }
})

// Expose focus method for parent to call after popup closes
defineExpose({ focusInput, scannerGunMode })
</script>

<style scoped>
.scanner-gun-active :deep(.q-field__control) {
  box-shadow: 0 0 0 2px var(--q-primary);
}
</style>
```

### 5.2 Page Integration

**File: `frontend/src/pages/ScanPage.vue`**

```vue
<script setup>
import { ref } from 'vue'
import BarcodeScanner from '../components/BarcodeScanner.vue'

const scannerRef = ref(null)

const handleConfirm = (formData) => {
  // ... confirmation logic ...
  
  // Restore scanner focus if in gun mode
  if (scannerRef.value?.scannerGunMode) {
    scannerRef.value.focusInput()
  }
}

const handleCancel = () => {
  // Restore scanner focus if in gun mode
  if (scannerRef.value?.scannerGunMode) {
    scannerRef.value.focusInput()
  }
}
</script>

<template>
  <BarcodeScanner ref="scannerRef" @scan="handleScan" />
</template>
```

### 5.3 State Persistence

State is persisted via localStorage in the Vue component (see `onMounted` and `toggleScannerGunMode` above).

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

- Vue's `ref.focus()` may need `nextTick()` after DOM updates
- Consider using `await nextTick()` before focus if needed
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
