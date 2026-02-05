/**
 * Navigation Tests
 */
import { test, expect } from '../fixtures/index.js'
import { NavigationComponent } from '../pages/components/navigation.js'
import { LoginPage } from '../pages/login.page.js'

test.describe('Navigation', () => {
  test.beforeEach(async ({ page, request, baseURL }) => {
    // Login first
    const health = await request.get(`${baseURL}/api/health`).catch(() => null)
    if (!health?.ok()) {
      test.skip(true, 'Backend not available')
    }

    const loginPage = new LoginPage(page)
    await loginPage.navigate()
    await loginPage.login('admin', 'test')
    await expect(page).toHaveURL(/\/scan/)
  })

  test.describe('Desktop Navigation', () => {
    test('header is visible', async ({ page }) => {
      const nav = new NavigationComponent(page)
      await expect(await nav.isHeaderVisible()).toBe(true)
    })

    test('can navigate to Products', async ({ page }) => {
      const nav = new NavigationComponent(page)
      await nav.navigateTo('products')
      await expect(page).toHaveURL(/\/products/)
    })

    test('can navigate to Inventory', async ({ page }) => {
      const nav = new NavigationComponent(page)
      await nav.navigateTo('inventory')
      await expect(page).toHaveURL(/\/inventory/)
    })

    test('can navigate to Locations', async ({ page }) => {
      const nav = new NavigationComponent(page)
      await nav.navigateTo('locations')
      await expect(page).toHaveURL(/\/locations/)
    })

    test('can navigate to Jobs', async ({ page }) => {
      const nav = new NavigationComponent(page)
      await nav.navigateTo('jobs')
      await expect(page).toHaveURL(/\/jobs/)
    })

    test('can navigate to Logs', async ({ page }) => {
      const nav = new NavigationComponent(page)
      await nav.navigateTo('logs')
      await expect(page).toHaveURL(/\/logs/)
    })

    test('can navigate to Settings', async ({ page }) => {
      const nav = new NavigationComponent(page)
      await nav.navigateTo('settings')
      await expect(page).toHaveURL(/\/settings/)
    })

    test('can navigate back to Scan', async ({ page }) => {
      const nav = new NavigationComponent(page)
      await nav.navigateTo('settings')
      await nav.navigateTo('scan')
      await expect(page).toHaveURL(/\/scan/)
    })
  })

  test.describe('Mobile Navigation', () => {
    test.use({ viewport: { width: 375, height: 667 } })

    test('mobile menu button is visible', async ({ page }) => {
      const nav = new NavigationComponent(page)
      const menuBtn = nav.mobileMenuBtn.or(page.locator('button').filter({ has: page.locator('.q-icon') }).first())
      await expect(menuBtn).toBeVisible()
    })

    test('can open mobile drawer', async ({ page }) => {
      const nav = new NavigationComponent(page)
      await nav.openMobileMenu()
      
      // Drawer should be visible
      const drawer = page.locator('.q-drawer')
      await expect(drawer).toBeVisible()
    })

    test('can navigate via mobile menu', async ({ page }) => {
      const nav = new NavigationComponent(page)
      await nav.navigateViaMobile('Products')
      await expect(page).toHaveURL(/\/products/)
    })

    test('drawer closes after navigation', async ({ page }) => {
      const nav = new NavigationComponent(page)
      await nav.navigateViaMobile('Products')
      
      // Drawer should close
      const drawer = page.locator('.q-drawer')
      await expect(drawer).not.toBeVisible()
    })
  })

  test.describe('Root Path Redirect', () => {
    test('root path redirects to scan when authenticated', async ({ page }) => {
      await page.goto('/')
      // Should either be on /scan or redirect there
      await expect(page).toHaveURL(/\/(scan|login)/)
    })
  })
})
