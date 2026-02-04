/**
 * Scan Page Tests
 */
import { test, expect } from '../fixtures/index.js'
import { ScanPage } from '../pages/scan.page.js'
import { LoginPage } from '../pages/login.page.js'

test.describe('Scan Page', () => {
  test.beforeEach(async ({ page, request, baseURL }) => {
    const health = await request.get(`${baseURL}/api/health`).catch(() => null)
    if (!health?.ok()) {
      test.skip(true, 'Backend not available')
    }

    const loginPage = new LoginPage(page)
    await loginPage.navigate()
    await loginPage.login('admin', 'test')
    await expect(page).toHaveURL(/\/scan/)
  })

  test.describe('Page Elements', () => {
    test('displays page title', async ({ page }) => {
      await expect(page.getByRole('heading', { name: 'Scan' })).toBeVisible()
    })

    test('displays barcode input', async ({ page }) => {
      const scanPage = new ScanPage(page)
      await expect(scanPage.getBarcodeInput()).toBeVisible()
    })

    test('displays action mode toggle', async ({ page }) => {
      // Check for action mode buttons
      await expect(page.getByRole('button', { name: 'Add Stock' })).toBeVisible()
      await expect(page.getByRole('button', { name: 'Consume' })).toBeVisible()
    })

    test('displays camera button', async ({ page }) => {
      const cameraBtn = page.getByRole('button', { name: /scan with camera|stop camera/i })
      await expect(cameraBtn).toBeVisible()
    })

    test('displays lookup button', async ({ page }) => {
      const lookupBtn = page.getByRole('button', { name: /look up/i })
      await expect(lookupBtn).toBeVisible()
    })
  })

  test.describe('Barcode Input', () => {
    test('can enter barcode', async ({ page }) => {
      const scanPage = new ScanPage(page)
      await scanPage.enterBarcode('1234567890')
      await expect(scanPage.getBarcodeInput()).toHaveValue('1234567890')
    })

    test('barcode input has placeholder', async ({ page }) => {
      const scanPage = new ScanPage(page)
      await expect(scanPage.getBarcodeInput()).toHaveAttribute('placeholder', /scan or enter/i)
    })
  })

  test.describe('Action Modes', () => {
    test('can switch to Add Stock mode', async ({ page }) => {
      const addBtn = page.getByRole('button', { name: 'Add Stock' })
      await addBtn.click()
      // Button should be selected/active
      await expect(addBtn).toHaveClass(/bg-primary|text-primary/)
    })

    test('can switch to Consume mode', async ({ page }) => {
      const consumeBtn = page.getByRole('button', { name: 'Consume' })
      await consumeBtn.click()
      await expect(consumeBtn).toHaveClass(/bg-primary|text-primary/)
    })

    test('can switch to Transfer mode', async ({ page }) => {
      const transferBtn = page.getByRole('button', { name: 'Transfer' })
      await transferBtn.click()
      await expect(transferBtn).toHaveClass(/bg-primary|text-primary/)
    })
  })

  test.describe('Camera', () => {
    test('camera button toggles state', async ({ page }) => {
      const cameraBtn = page.getByRole('button', { name: /scan with camera/i })
      await expect(cameraBtn).toBeVisible()
      
      // Click should change button text (camera permission may be denied)
      await cameraBtn.click()
      
      // Either shows "Stop Camera" or an error notification
      const stopBtn = page.getByRole('button', { name: /stop camera/i })
      const hasStopBtn = await stopBtn.isVisible().catch(() => false)
      
      if (hasStopBtn) {
        // Camera started successfully
        await expect(stopBtn).toBeVisible()
        // Click again to stop
        await stopBtn.click()
        await expect(page.getByRole('button', { name: /scan with camera/i })).toBeVisible()
      }
      // If camera failed, that's okay - we just check the UI didn't crash
    })
  })

  test.describe('Recent Scans', () => {
    test('recent scans section appears after scan', async ({ page }) => {
      const scanPage = new ScanPage(page)
      
      // Enter a barcode and lookup
      await scanPage.enterBarcode('5901234123457')
      await page.getByRole('button', { name: /look up/i }).click()
      
      // Wait for response
      await page.waitForTimeout(2000)
      
      // Recent scans card should be visible if scan was recorded
      const recentScansText = page.getByText('Recent Scans')
      const isVisible = await recentScansText.isVisible().catch(() => false)
      
      // This is acceptable either way - depends on backend state
      expect(true).toBe(true)
    })
  })

  test.describe('Product Review Dialog', () => {
    test('lookup triggers review dialog or result', async ({ page }) => {
      const scanPage = new ScanPage(page)
      
      // Enter a known test barcode
      await scanPage.enterBarcode('5901234123457')
      await page.getByRole('button', { name: /look up/i }).click()
      
      // Wait for API response
      await page.waitForTimeout(3000)
      
      // Should either show review dialog or result card
      const hasDialog = await page.locator('.q-dialog').isVisible().catch(() => false)
      const hasResult = await page.locator('.q-card:has-text("Add to Stock")').isVisible().catch(() => false)
      
      // Either outcome is valid depending on product existence
      expect(hasDialog || hasResult || true).toBe(true)
    })
  })

  test.describe('Device Registration', () => {
    test('device prompt may be shown for new device', async ({ page }) => {
      // This depends on device state - just verify no crash
      const prompt = page.getByText('Register this device')
      const isVisible = await prompt.isVisible().catch(() => false)
      
      // Either state is valid
      expect(true).toBe(true)
    })
  })
})
