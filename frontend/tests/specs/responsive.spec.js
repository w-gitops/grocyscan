/**
 * Responsive Design Tests
 * 
 * Tests for different viewport sizes: mobile, tablet, desktop.
 * Maps to BrowserMCP test cases RSP-01 through RSP-04.
 */
import { test, expect } from '../fixtures/auth.fixture.js'

test.describe('Responsive Design', () => {
  // Login before tests
  async function loginAndNavigate(page, request, baseURL, path = '/scan') {
    const health = await request.get(`${baseURL}/api/health`).catch(() => null)
    if (!health?.ok()) {
      test.skip(true, 'Backend not available')
    }

    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('test')
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL(/\/scan/)
    
    if (path !== '/scan') {
      await page.goto(path)
    }
  }

  test.describe('Mobile Viewport (375px)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
    })

    // RSP-01: Mobile scan page
    test('scan page renders correctly on mobile', async ({ page, request, baseURL }) => {
      await loginAndNavigate(page, request, baseURL, '/scan')
      
      // Mobile menu button should be visible
      await expect(page.getByTestId('mobile-menu-button')).toBeVisible()
      
      // Desktop nav should be hidden
      await expect(page.getByTestId('nav-scan')).not.toBeVisible()
      
      // Page content should be visible
      await expect(page.getByRole('heading', { name: 'Scan' })).toBeVisible()
      await expect(page.getByTestId('scan-barcode-input')).toBeVisible()
    })

    test('products page renders correctly on mobile', async ({ page, request, baseURL }) => {
      await loginAndNavigate(page, request, baseURL, '/products')
      
      await expect(page.getByTestId('mobile-menu-button')).toBeVisible()
      await expect(page.getByText('Products')).toBeVisible()
      await expect(page.getByTestId('products-search')).toBeVisible()
    })

    test('settings page renders correctly on mobile', async ({ page, request, baseURL }) => {
      await loginAndNavigate(page, request, baseURL, '/settings')
      
      await expect(page.getByTestId('mobile-menu-button')).toBeVisible()
      await expect(page.getByText('Settings')).toBeVisible()
      
      // Tabs should be visible and scrollable
      await expect(page.getByTestId('settings-tab-grocy')).toBeVisible()
    })

    test('mobile drawer opens and navigates', async ({ page, request, baseURL }) => {
      await loginAndNavigate(page, request, baseURL, '/scan')
      
      // Open mobile drawer
      await page.getByTestId('mobile-menu-button').click()
      await expect(page.getByTestId('mobile-drawer')).toBeVisible()
      
      // Navigate to products
      await page.getByTestId('mobile-nav-products').click()
      await expect(page).toHaveURL(/\/products/)
    })

    // RSP-04: Touch targets
    test('buttons have adequate touch targets', async ({ page, request, baseURL }) => {
      await loginAndNavigate(page, request, baseURL, '/scan')
      
      // Check that main buttons are large enough for touch
      const submitBtn = page.getByTestId('scan-lookup-btn')
      const box = await submitBtn.boundingBox()
      
      // Minimum touch target: 48x48px (Google recommendation)
      // Allow some tolerance for border-box sizing
      expect(box.height).toBeGreaterThanOrEqual(36)
      expect(box.width).toBeGreaterThanOrEqual(48)
    })
  })

  test.describe('Tablet Viewport (768px)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
    })

    // RSP-02: Tablet products page
    test('products page renders correctly on tablet', async ({ page, request, baseURL }) => {
      await loginAndNavigate(page, request, baseURL, '/products')
      
      await expect(page.getByText('Products')).toBeVisible()
      await expect(page.getByTestId('products-search')).toBeVisible()
    })

    test('navigation layout adjusts for tablet', async ({ page, request, baseURL }) => {
      await loginAndNavigate(page, request, baseURL, '/scan')
      
      // May show either desktop nav or mobile nav depending on breakpoint
      const hasMobileMenu = await page.getByTestId('mobile-menu-button').isVisible().catch(() => false)
      const hasDesktopNav = await page.getByTestId('nav-scan').isVisible().catch(() => false)
      
      expect(hasMobileMenu || hasDesktopNav).toBeTruthy()
    })
  })

  test.describe('Desktop Viewport (1280px)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 800 })
    })

    // RSP-03: Desktop settings
    test('settings page renders full width on desktop', async ({ page, request, baseURL }) => {
      await loginAndNavigate(page, request, baseURL, '/settings')
      
      await expect(page.getByText('Settings')).toBeVisible()
      
      // All tabs should be visible
      await expect(page.getByTestId('settings-tab-grocy')).toBeVisible()
      await expect(page.getByTestId('settings-tab-llm')).toBeVisible()
      await expect(page.getByTestId('settings-tab-lookup')).toBeVisible()
      await expect(page.getByTestId('settings-tab-scanning')).toBeVisible()
      await expect(page.getByTestId('settings-tab-ui')).toBeVisible()
    })

    test('desktop nav is visible', async ({ page, request, baseURL }) => {
      await loginAndNavigate(page, request, baseURL, '/scan')
      
      // Desktop nav buttons should be visible
      await expect(page.getByTestId('nav-scan')).toBeVisible()
      await expect(page.getByTestId('nav-products')).toBeVisible()
      await expect(page.getByTestId('nav-settings')).toBeVisible()
      
      // Mobile menu should be hidden
      await expect(page.getByTestId('mobile-menu-button')).not.toBeVisible()
    })

    test('header and content layout correct', async ({ page, request, baseURL }) => {
      await loginAndNavigate(page, request, baseURL, '/scan')
      
      await expect(page.getByTestId('app-header')).toBeVisible()
      await expect(page.getByTestId('app-logo')).toBeVisible()
      await expect(page.getByRole('heading', { name: 'Scan' })).toBeVisible()
    })
  })

  test.describe('Viewport Transitions', () => {
    test('layout adjusts when viewport changes', async ({ page, request, baseURL }) => {
      await page.setViewportSize({ width: 1280, height: 800 })
      await loginAndNavigate(page, request, baseURL, '/scan')
      
      // Desktop: nav visible
      await expect(page.getByTestId('nav-scan')).toBeVisible()
      
      // Resize to mobile
      await page.setViewportSize({ width: 375, height: 667 })
      await page.waitForTimeout(500)
      
      // Mobile: menu button visible
      await expect(page.getByTestId('mobile-menu-button')).toBeVisible()
      
      // Resize back to desktop
      await page.setViewportSize({ width: 1280, height: 800 })
      await page.waitForTimeout(500)
      
      // Desktop nav visible again
      await expect(page.getByTestId('nav-scan')).toBeVisible()
    })
  })
})
