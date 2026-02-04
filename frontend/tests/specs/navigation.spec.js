/**
 * Navigation Tests
 * 
 * Tests for header navigation, mobile drawer, and routing.
 * Maps to BrowserMCP test cases NAV-01 through NAV-12.
 */
import { test, expect } from '../fixtures/auth.fixture.js'
import { NavigationComponent } from '../pages/components/navigation.js'

test.describe('Navigation', () => {
  // Skip all navigation tests if backend unavailable
  test.beforeEach(async ({ page, request, baseURL }) => {
    const health = await request.get(`${baseURL}/api/health`).catch(() => null)
    if (!health?.ok()) {
      test.skip(true, 'Backend not available')
    }

    // Login first
    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('test')
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL(/\/scan/)
  })

  test.describe('Header Navigation (Desktop)', () => {
    // NAV-01: Header visibility
    test('displays header with logo and nav buttons', async ({ page }) => {
      await expect(page.getByTestId('app-header')).toBeVisible()
      await expect(page.getByTestId('app-logo')).toBeVisible()
    })

    // NAV-02: Navigate to Scan
    test('navigates to Scan page', async ({ page }) => {
      await page.getByTestId('nav-scan').click()
      await expect(page).toHaveURL(/\/scan/)
      await expect(page.getByRole('heading', { name: 'Scan' })).toBeVisible()
    })

    // NAV-03: Navigate to Products
    test('navigates to Products page', async ({ page }) => {
      await page.getByTestId('nav-products').click()
      await expect(page).toHaveURL(/\/products/)
      await expect(page.getByText('Products')).toBeVisible()
    })

    // NAV-04: Navigate to Inventory
    test('navigates to Inventory page', async ({ page }) => {
      await page.getByTestId('nav-inventory').click()
      await expect(page).toHaveURL(/\/inventory/)
    })

    // NAV-05: Navigate to Locations
    test('navigates to Locations page', async ({ page }) => {
      await page.getByTestId('nav-locations').click()
      await expect(page).toHaveURL(/\/locations/)
      await expect(page.getByText('Locations')).toBeVisible()
    })

    // NAV-06: Navigate to Jobs
    test('navigates to Jobs page', async ({ page }) => {
      await page.getByTestId('nav-jobs').click()
      await expect(page).toHaveURL(/\/jobs/)
    })

    // NAV-07: Navigate to Logs
    test('navigates to Logs page', async ({ page }) => {
      await page.getByTestId('nav-logs').click()
      await expect(page).toHaveURL(/\/logs/)
    })

    // NAV-08: Navigate to Settings
    test('navigates to Settings page', async ({ page }) => {
      await page.getByTestId('nav-settings').click()
      await expect(page).toHaveURL(/\/settings/)
      await expect(page.getByText('Settings')).toBeVisible()
    })

    // NAV-09: Root redirect
    test('root path redirects to /scan', async ({ page }) => {
      await page.goto('/')
      await expect(page).toHaveURL(/\/scan/)
    })

    // Logout button visible when authenticated
    test('shows logout button when authenticated', async ({ page }) => {
      await expect(page.getByTestId('logout-button')).toBeVisible()
    })
  })

  test.describe('Mobile Navigation', () => {
    test.beforeEach(async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 })
    })

    // NAV-10: Mobile menu button visible
    test('shows mobile menu button at small viewport', async ({ page }) => {
      await expect(page.getByTestId('mobile-menu-button')).toBeVisible()
    })

    // NAV-11: Mobile drawer opens
    test('opens mobile drawer when menu button clicked', async ({ page }) => {
      await page.getByTestId('mobile-menu-button').click()
      await expect(page.getByTestId('mobile-drawer')).toBeVisible()
    })

    // NAV-12: Mobile nav to Scan
    test('navigates to Scan via mobile drawer', async ({ page }) => {
      await page.getByTestId('mobile-menu-button').click()
      await page.getByTestId('mobile-nav-scan').click()
      await expect(page).toHaveURL(/\/scan/)
    })

    test('navigates to Products via mobile drawer', async ({ page }) => {
      await page.getByTestId('mobile-menu-button').click()
      await page.getByTestId('mobile-nav-products').click()
      await expect(page).toHaveURL(/\/products/)
    })

    test('navigates to Settings via mobile drawer', async ({ page }) => {
      await page.getByTestId('mobile-menu-button').click()
      await page.getByTestId('mobile-nav-settings').click()
      await expect(page).toHaveURL(/\/settings/)
    })

    test('navigates to Locations via mobile drawer', async ({ page }) => {
      await page.getByTestId('mobile-menu-button').click()
      await page.getByTestId('mobile-nav-locations').click()
      await expect(page).toHaveURL(/\/locations/)
    })

    test('navigates to Jobs via mobile drawer', async ({ page }) => {
      await page.getByTestId('mobile-menu-button').click()
      await page.getByTestId('mobile-nav-jobs').click()
      await expect(page).toHaveURL(/\/jobs/)
    })

    test('navigates to Logs via mobile drawer', async ({ page }) => {
      await page.getByTestId('mobile-menu-button').click()
      await page.getByTestId('mobile-nav-logs').click()
      await expect(page).toHaveURL(/\/logs/)
    })
  })

  test.describe('Navigation State', () => {
    test('navigation persists across page loads', async ({ page }) => {
      // Navigate to settings
      await page.getByTestId('nav-settings').click()
      await expect(page).toHaveURL(/\/settings/)

      // Reload and verify still on settings
      await page.reload()
      await expect(page).toHaveURL(/\/settings/)
    })
  })
})
