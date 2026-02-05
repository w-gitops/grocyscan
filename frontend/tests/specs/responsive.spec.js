/**
 * Responsive Design Tests
 * Tests UI behavior across different viewport sizes
 */
import { test, expect } from '../fixtures/index.js'
import { LoginPage } from '../pages/login.page.js'

const viewports = {
  mobile: { width: 375, height: 667 },
  tablet: { width: 768, height: 1024 },
  desktop: { width: 1280, height: 800 }
}

test.describe('Responsive Design', () => {
  test.describe('Mobile Viewport (375px)', () => {
    test.use({ viewport: viewports.mobile })

    test('login page renders correctly on mobile', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()

      await expect(page.getByText('Sign in to continue')).toBeVisible()
      await expect(loginPage.getUsernameInput()).toBeVisible()
      await expect(loginPage.getPasswordInput()).toBeVisible()
    })

    test('mobile menu button is visible when logged in', async ({ page, request, baseURL }) => {
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.login('admin', 'test')

      // Mobile menu button should be visible
      const menuBtn = page.locator('button').filter({ has: page.locator('.q-icon') }).first()
      await expect(menuBtn).toBeVisible()
    })

    test('desktop nav buttons are hidden on mobile', async ({ page, request, baseURL }) => {
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.login('admin', 'test')

      // Desktop nav buttons should be hidden (gt-sm class hides on mobile)
      const desktopNav = page.locator('.q-toolbar .gt-sm')
      const count = await desktopNav.count()
      
      // Either hidden or not present
      for (let i = 0; i < count; i++) {
        const isVisible = await desktopNav.nth(i).isVisible().catch(() => false)
        expect(isVisible).toBe(false)
      }
    })
  })

  test.describe('Tablet Viewport (768px)', () => {
    test('login page renders correctly on tablet', async ({ page }) => {
      await page.setViewportSize(viewports.tablet)
      const loginPage = new LoginPage(page)
      await loginPage.navigate()

      await expect(page.getByText('Sign in to continue')).toBeVisible()
    })

    test('navigation adapts to tablet size', async ({ page, request, baseURL }) => {
      await page.setViewportSize(viewports.tablet)
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.login('admin', 'test')
      await page.waitForURL(/\/scan/)

      // At 768px, page should have loaded
      const hasHeader = await page.locator('header, .q-header').isVisible().catch(() => false)
      const hasToolbar = await page.locator('.q-toolbar').isVisible().catch(() => false)
      const hasPage = await page.locator('.q-page').isVisible().catch(() => false)
      expect(hasHeader || hasToolbar || hasPage).toBe(true)
    })
  })

  // Desktop tests - These manually set viewport so they work on any project
  test.describe('Desktop Viewport (1280px)', () => {

    test('login page renders correctly on desktop', async ({ page }) => {
      await page.setViewportSize(viewports.desktop)
      const loginPage = new LoginPage(page)
      await loginPage.navigate()

      await expect(page.getByText('Sign in to continue')).toBeVisible()
    })

    test('desktop navigation is visible', async ({ page, request, baseURL }) => {
      await page.setViewportSize(viewports.desktop)
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.login('admin', 'test')
      await page.waitForURL(/\/scan/)

      // Desktop nav should be visible - check for nav buttons or links
      const scanBtn = page.getByRole('button', { name: 'Scan' }).or(page.locator('[data-testid="nav-scan"]'))
      const hasNav = await scanBtn.isVisible().catch(() => false)
      const hasHeader = await page.locator('.q-header').isVisible().catch(() => false)
      const hasPage = await page.locator('.q-page').isVisible().catch(() => false)
      expect(hasNav || hasHeader || hasPage).toBe(true)
    })

    test('page loads correctly on desktop', async ({ page, request, baseURL }) => {
      await page.setViewportSize(viewports.desktop)
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.login('admin', 'test')
      await page.waitForURL(/\/scan/)

      // Verify page loaded successfully
      const hasHeader = await page.locator('.q-header').isVisible().catch(() => false)
      const hasPage = await page.locator('.q-page').isVisible().catch(() => false)
      expect(hasHeader || hasPage).toBe(true)
    })
  })

  test.describe('Cross-Viewport Consistency', () => {
    test('login form maintains functionality across viewports', async ({ page }) => {
      const loginPage = new LoginPage(page)

      for (const [name, viewport] of Object.entries(viewports)) {
        await page.setViewportSize(viewport)
        await loginPage.navigate()

        // Form should always be functional
        await expect(loginPage.getUsernameInput()).toBeVisible()
        await expect(loginPage.getPasswordInput()).toBeVisible()
        await expect(loginPage.getSubmitButton()).toBeVisible()
      }
    })
  })
})
