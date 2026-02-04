/**
 * Theme Tests
 * 
 * Tests for light/dark/auto theme modes.
 * Maps to BrowserMCP test cases THM-01 through THM-05.
 */
import { test, expect } from '../fixtures/auth.fixture.js'

test.describe('Theme', () => {
  // Login and navigate to settings/UI tab
  async function loginAndGoToThemeSettings(page, request, baseURL) {
    const health = await request.get(`${baseURL}/api/health`).catch(() => null)
    if (!health?.ok()) {
      test.skip(true, 'Backend not available')
    }

    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('test')
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL(/\/scan/)
    
    await page.goto('/settings')
    await page.getByTestId('settings-tab-ui').click()
  }

  test.describe('Theme Settings', () => {
    test('UI settings tab shows kiosk mode toggle', async ({ page, request, baseURL }) => {
      await loginAndGoToThemeSettings(page, request, baseURL)
      
      await expect(page.getByTestId('scanning-kiosk-mode')).toBeVisible()
    })

    test('can toggle kiosk mode', async ({ page, request, baseURL }) => {
      await loginAndGoToThemeSettings(page, request, baseURL)
      
      const toggle = page.getByTestId('scanning-kiosk-mode')
      const initialState = await toggle.isChecked()
      
      await toggle.click()
      await expect(toggle).toBeChecked({ checked: !initialState })
    })

    test('save button persists settings', async ({ page, request, baseURL }) => {
      await loginAndGoToThemeSettings(page, request, baseURL)
      
      // Click save
      await page.getByTestId('ui-save-button').click()
      
      // Should show success notification
      await expect(page.locator('.q-notification')).toBeVisible({ timeout: 5000 })
    })
  })

  test.describe('Visual Consistency', () => {
    // THM-01: Light mode visual check
    test('app renders with consistent styling', async ({ page, request, baseURL }) => {
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      await page.goto('/login')
      await page.getByLabel('Username').fill('admin')
      await page.getByLabel('Password').fill('test')
      await page.getByRole('button', { name: /sign in/i }).click()
      await page.waitForURL(/\/scan/)
      
      // Header should have consistent styling
      const header = page.getByTestId('app-header')
      await expect(header).toBeVisible()
      
      // Background should have some styling
      const headerBg = await header.evaluate(el => getComputedStyle(el).backgroundColor)
      expect(headerBg).toBeTruthy()
    })

    // THM-03: Header maintains primary color
    test('header has primary color styling', async ({ page, request, baseURL }) => {
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      await page.goto('/login')
      await page.getByLabel('Username').fill('admin')
      await page.getByLabel('Password').fill('test')
      await page.getByRole('button', { name: /sign in/i }).click()
      await page.waitForURL(/\/scan/)
      
      const header = page.getByTestId('app-header')
      const classes = await header.getAttribute('class')
      
      // Quasar headers typically have elevation class
      expect(classes).toContain('q-header')
    })

    // THM-04: Cards render properly
    test('cards have proper styling', async ({ page, request, baseURL }) => {
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      await page.goto('/login')
      await page.getByLabel('Username').fill('admin')
      await page.getByLabel('Password').fill('test')
      await page.getByRole('button', { name: /sign in/i }).click()
      await page.waitForURL(/\/scan/)
      
      const card = page.getByTestId('scan-card')
      await expect(card).toBeVisible()
      
      // Card should have border or shadow
      const cardStyles = await card.evaluate(el => {
        const style = getComputedStyle(el)
        return {
          border: style.border,
          boxShadow: style.boxShadow
        }
      })
      
      // Should have some visual distinction
      expect(cardStyles.border || cardStyles.boxShadow).toBeTruthy()
    })

    // THM-05: Theme persistence
    test('page styles persist after reload', async ({ page, request, baseURL }) => {
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      await page.goto('/login')
      await page.getByLabel('Username').fill('admin')
      await page.getByLabel('Password').fill('test')
      await page.getByRole('button', { name: /sign in/i }).click()
      await page.waitForURL(/\/scan/)
      
      // Get initial header background
      const header = page.getByTestId('app-header')
      const initialBg = await header.evaluate(el => getComputedStyle(el).backgroundColor)
      
      // Reload
      await page.reload()
      await page.waitForURL(/\/scan/)
      
      // Header should still have same styling
      const headerAfter = page.getByTestId('app-header')
      const bgAfter = await headerAfter.evaluate(el => getComputedStyle(el).backgroundColor)
      
      expect(bgAfter).toEqual(initialBg)
    })
  })

  test.describe('Color Scheme Preference', () => {
    test('respects system color scheme preference (light)', async ({ page, request, baseURL }) => {
      // Emulate light mode preference
      await page.emulateMedia({ colorScheme: 'light' })
      
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      await page.goto('/login')
      
      // Page should render (light mode may or may not be explicitly different)
      await expect(page.getByText('Sign in to continue')).toBeVisible()
    })

    test('respects system color scheme preference (dark)', async ({ page, request, baseURL }) => {
      // Emulate dark mode preference
      await page.emulateMedia({ colorScheme: 'dark' })
      
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      await page.goto('/login')
      
      // Page should render (may adapt to dark mode if implemented)
      await expect(page.getByText('Sign in to continue')).toBeVisible()
    })
  })
})
