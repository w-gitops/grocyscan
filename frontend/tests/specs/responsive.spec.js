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
    test.use({ viewport: viewports.tablet })

    test('login page renders correctly on tablet', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()

      await expect(page.getByText('Sign in to continue')).toBeVisible()
    })

    test('navigation adapts to tablet size', async ({ page, request, baseURL }) => {
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.login('admin', 'test')

      // At 768px, may show mobile menu or partial desktop nav
      const hasHeader = await page.locator('header').isVisible()
      expect(hasHeader).toBe(true)
    })
  })

  test.describe('Desktop Viewport (1280px)', () => {
    test.use({ viewport: viewports.desktop })

    test('login page renders correctly on desktop', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()

      await expect(page.getByText('Sign in to continue')).toBeVisible()
    })

    test('desktop navigation is visible', async ({ page, request, baseURL }) => {
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.login('admin', 'test')

      // Desktop nav should be visible
      const scanBtn = page.getByRole('button', { name: 'Scan' })
      await expect(scanBtn).toBeVisible()

      const productsBtn = page.getByRole('button', { name: 'Products' })
      await expect(productsBtn).toBeVisible()
    })

    test('mobile menu button is hidden on desktop', async ({ page, request, baseURL }) => {
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.login('admin', 'test')

      // Mobile menu button (lt-md class) should be hidden
      const mobileMenuBtn = page.locator('.lt-md')
      const count = await mobileMenuBtn.count()
      
      for (let i = 0; i < count; i++) {
        const isVisible = await mobileMenuBtn.nth(i).isVisible().catch(() => false)
        expect(isVisible).toBe(false)
      }
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
