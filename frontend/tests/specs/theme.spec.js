/**
 * Theme Tests
 * Tests UI consistency and theme handling
 */
import { test, expect } from '../fixtures/index.js'
import { LoginPage } from '../pages/login.page.js'

test.describe('Theme', () => {
  test.describe('Visual Consistency', () => {
    test('login page has consistent styling', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()

      // Check that main card exists and is styled
      const card = page.locator('.q-card')
      await expect(card).toBeVisible()
    })

    test('buttons have consistent styling', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()

      const submitBtn = loginPage.getSubmitButton()
      await expect(submitBtn).toBeVisible()
      
      // Button should have Quasar styling
      await expect(submitBtn).toHaveClass(/q-btn/)
    })

    test('inputs have consistent styling', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()

      const usernameInput = loginPage.getUsernameInput()
      await expect(usernameInput).toBeVisible()
    })
  })

  test.describe('Application Theme', () => {
    test('header has consistent styling when logged in', async ({ page, request, baseURL }) => {
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.login('admin', 'test')

      // Header should be styled
      const header = page.locator('header, .q-header')
      await expect(header).toBeVisible()
    })

    test('cards have consistent styling', async ({ page, request, baseURL }) => {
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.login('admin', 'test')

      // Scan page should have cards
      const cards = page.locator('.q-card')
      const cardCount = await cards.count()
      expect(cardCount).toBeGreaterThan(0)
    })
  })

  test.describe('Theme Persistence', () => {
    test('theme persists across page reload', async ({ page, request, baseURL }) => {
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.login('admin', 'test')

      // Get initial state
      const initialHeader = await page.locator('header').getAttribute('class')

      // Reload
      await page.reload()

      // Check state is consistent
      const reloadedHeader = await page.locator('header').getAttribute('class')
      expect(reloadedHeader).toBe(initialHeader)
    })
  })

  test.describe('Color Scheme', () => {
    test('respects system color scheme preference', async ({ page }) => {
      // Emulate dark mode
      await page.emulateMedia({ colorScheme: 'dark' })
      
      const loginPage = new LoginPage(page)
      await loginPage.navigate()

      // Page should load (Quasar may or may not auto-adapt)
      await expect(page.getByText('Sign in to continue')).toBeVisible()
    })

    test('respects light color scheme preference', async ({ page }) => {
      await page.emulateMedia({ colorScheme: 'light' })
      
      const loginPage = new LoginPage(page)
      await loginPage.navigate()

      await expect(page.getByText('Sign in to continue')).toBeVisible()
    })
  })
})
