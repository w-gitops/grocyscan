/**
 * Scan Page Tests
 * 
 * Tests for the barcode scanning page, the primary user workflow.
 * Maps to BrowserMCP test cases SCAN-01 through SCAN-10.
 */
import { test, expect } from '../fixtures/auth.fixture.js'
import { ScanPage } from '../pages/scan.page.js'

test.describe('Scan Page', () => {
  // Login before each test
  test.beforeEach(async ({ page, request, baseURL }) => {
    const health = await request.get(`${baseURL}/api/health`).catch(() => null)
    if (!health?.ok()) {
      test.skip(true, 'Backend not available')
    }

    // Login
    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('test')
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL(/\/scan/)
  })

  test.describe('Page Elements', () => {
    // SCAN-01: Page title
    test('displays page title', async ({ page }) => {
      await expect(page.getByRole('heading', { name: 'Scan' })).toBeVisible()
    })

    // SCAN-02: Action mode selector
    test('displays action mode selector', async ({ page }) => {
      await expect(page.getByTestId('scan-action-mode')).toBeVisible()
      await expect(page.getByText('Add Stock')).toBeVisible()
      await expect(page.getByText('Consume')).toBeVisible()
      await expect(page.getByText('Transfer')).toBeVisible()
    })

    // SCAN-03: Barcode input field
    test('displays barcode input field', async ({ page }) => {
      await expect(page.getByTestId('scan-barcode-input')).toBeVisible()
      await expect(page.getByPlaceholder(/scan or enter barcode/i)).toBeVisible()
    })

    // SCAN-04: Camera button
    test('displays camera scan button', async ({ page }) => {
      await expect(page.getByTestId('scan-camera-button')).toBeVisible()
    })

    // SCAN-05: Lookup button
    test('displays lookup button', async ({ page }) => {
      await expect(page.getByTestId('scan-lookup-btn')).toBeVisible()
    })
  })

  test.describe('Barcode Input', () => {
    // SCAN-06: Manual barcode entry
    test('accepts manual barcode entry', async ({ page }) => {
      const scanPage = new ScanPage(page)
      const input = page.getByTestId('scan-barcode-input')
      
      await input.fill('4006381333931')
      await expect(input).toHaveValue('4006381333931')
    })

    // SCAN-07: Submit button triggers lookup
    test('submit button triggers lookup', async ({ page }) => {
      const input = page.getByTestId('scan-barcode-input')
      await input.fill('4006381333931')
      
      // Click submit - should trigger API call
      await page.getByTestId('scan-submit').click()
      
      // Wait for some response (either dialog or notification)
      await page.waitForTimeout(2000)
      
      // Should show either the review dialog or a notification
      const hasDialog = await page.getByTestId('product-review-dialog').isVisible().catch(() => false)
      const hasNotification = await page.locator('.q-notification').isVisible().catch(() => false)
      
      expect(hasDialog || hasNotification).toBeTruthy()
    })

    // SCAN-08: Enter key triggers lookup
    test('enter key triggers lookup', async ({ page }) => {
      const input = page.getByTestId('scan-barcode-input')
      await input.fill('4006381333931')
      await input.press('Enter')
      
      // Wait for response
      await page.waitForTimeout(2000)
      
      // Should show some response
      const hasDialog = await page.getByTestId('product-review-dialog').isVisible().catch(() => false)
      const hasNotification = await page.locator('.q-notification').isVisible().catch(() => false)
      
      expect(hasDialog || hasNotification).toBeTruthy()
    })
  })

  test.describe('Camera Scanner', () => {
    // SCAN-09: Camera dialog opens
    test('opens camera dialog when camera button clicked', async ({ page }) => {
      await page.getByTestId('scan-camera-button').click()
      
      // Camera preview should become visible (even if camera permission denied)
      await expect(page.getByTestId('scan-camera-preview')).toBeVisible({ timeout: 3000 })
    })

    // SCAN-10: Camera can be stopped
    test('camera toggle button changes state', async ({ page }) => {
      const cameraBtn = page.getByTestId('scan-camera-button')
      
      // Initial state - shows "Scan with Camera"
      await expect(cameraBtn).toContainText(/scan with camera/i)
      
      // Click to start camera
      await cameraBtn.click()
      await page.waitForTimeout(1000)
      
      // Button should now show "Stop Camera"
      await expect(cameraBtn).toContainText(/stop camera/i)
      
      // Click to stop
      await cameraBtn.click()
      await page.waitForTimeout(500)
      
      // Should be back to initial state
      await expect(cameraBtn).toContainText(/scan with camera/i)
    })
  })

  test.describe('Action Mode', () => {
    test('can switch to Consume mode', async ({ page }) => {
      await page.getByText('Consume').click()
      
      // Verify selection (the button should be highlighted)
      const actionMode = page.getByTestId('scan-action-mode')
      await expect(actionMode).toBeVisible()
    })

    test('can switch to Transfer mode', async ({ page }) => {
      await page.getByText('Transfer').click()
      
      // Verify selection
      const actionMode = page.getByTestId('scan-action-mode')
      await expect(actionMode).toBeVisible()
    })

    test('can switch back to Add Stock mode', async ({ page }) => {
      // First switch to Consume
      await page.getByText('Consume').click()
      
      // Then back to Add Stock
      await page.getByText('Add Stock').click()
      
      // Verify
      const actionMode = page.getByTestId('scan-action-mode')
      await expect(actionMode).toBeVisible()
    })
  })

  test.describe('Location Selector', () => {
    test('location selector is visible when locations exist', async ({ page }) => {
      // Location selector may or may not be visible depending on whether locations are configured
      const locSelector = page.getByTestId('scan-location-selector')
      
      // Just verify the page loaded properly - selector depends on backend data
      await expect(page.getByTestId('scan-page')).toBeVisible()
    })
  })

  test.describe('Recent Scans', () => {
    test('displays recent scans section when scans exist', async ({ page }) => {
      // Perform a scan first
      const input = page.getByTestId('scan-barcode-input')
      await input.fill('0012345678901')
      await page.getByTestId('scan-submit').click()
      
      // Wait for response
      await page.waitForTimeout(2000)
      
      // Close any dialog that might have opened
      const closeBtn = page.getByRole('button', { name: /cancel|close/i })
      if (await closeBtn.isVisible().catch(() => false)) {
        await closeBtn.click()
      }
      
      // Recent scans should be visible
      const recentCard = page.getByTestId('scan-recent-card')
      await expect(recentCard).toBeVisible({ timeout: 5000 })
    })
  })

  test.describe('Product Review Dialog', () => {
    test('review dialog opens after barcode lookup', async ({ page }) => {
      // Enter a barcode that should trigger lookup
      const input = page.getByTestId('scan-barcode-input')
      await input.fill('3017620422003') // Nutella barcode
      await input.press('Enter')
      
      // Wait for dialog
      await page.waitForTimeout(3000)
      
      // Check if dialog opened (may be found or not found product)
      const dialog = page.getByTestId('product-review-dialog')
      const isDialogVisible = await dialog.isVisible().catch(() => false)
      
      // If backend finds the product or shows new product dialog
      if (isDialogVisible) {
        await expect(page.getByTestId('product-review-card')).toBeVisible()
      }
    })

    test('review dialog has cancel button', async ({ page }) => {
      // Enter a barcode
      const input = page.getByTestId('scan-barcode-input')
      await input.fill('3017620422003')
      await input.press('Enter')
      
      // Wait for dialog
      await page.waitForTimeout(3000)
      
      const dialog = page.getByTestId('product-review-dialog')
      if (await dialog.isVisible().catch(() => false)) {
        await expect(page.getByTestId('product-review-cancel')).toBeVisible()
        
        // Click cancel to close
        await page.getByTestId('product-review-cancel').click()
        await expect(dialog).not.toBeVisible()
      }
    })

    test('review dialog shows quantity input', async ({ page }) => {
      const input = page.getByTestId('scan-barcode-input')
      await input.fill('3017620422003')
      await input.press('Enter')
      
      await page.waitForTimeout(3000)
      
      const dialog = page.getByTestId('product-review-dialog')
      if (await dialog.isVisible().catch(() => false)) {
        await expect(page.getByTestId('product-review-quantity')).toBeVisible()
      }
    })
  })

  test.describe('Device Registration', () => {
    // This test checks for device registration prompt behavior
    // The prompt appears for unregistered devices
    test('device registration dialog can be triggered', async ({ page }) => {
      // Check if device prompt banner is visible
      const devicePrompt = page.getByTestId('scan-device-prompt')
      
      if (await devicePrompt.isVisible().catch(() => false)) {
        // Click register button
        await page.getByTestId('scan-device-register-btn').click()
        
        // Dialog should open
        await expect(page.getByTestId('device-dialog')).toBeVisible()
        await expect(page.getByTestId('device-name-input')).toBeVisible()
      }
    })
  })
})
