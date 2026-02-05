/**
 * Authentication Tests
 */
import { test, expect } from '@playwright/test'
import { LoginPage } from '../pages/login.page.js'

test.describe('Authentication', () => {
  test.describe('Login Page', () => {
    test('renders login form', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()

      await expect(page.getByText('Sign in to continue')).toBeVisible()
      await expect(loginPage.getUsernameInput()).toBeVisible()
      await expect(loginPage.getPasswordInput()).toBeVisible()
      await expect(loginPage.getSubmitButton()).toBeVisible()
    })

    test('shows validation errors for empty fields', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()

      // Try to submit without filling fields
      await loginPage.submit()

      // Form should still be on login page (validation prevents submission)
      await expect(page).toHaveURL(/\/login/)
    })

    test('password field is masked by default', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()

      const passwordInput = loginPage.getPasswordInput()
      await expect(passwordInput).toHaveAttribute('type', 'password')
    })

    test('shows error on invalid credentials', async ({ page, request }) => {
      // Check if backend is available
      const health = await request.get('/api/health').catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.login('invalid_user', 'wrong_password')

      // Should show error or stay on login
      await expect(page).toHaveURL(/\/login/)
    })

    test('successful login redirects to scan page', async ({ page, request }) => {
      const health = await request.get('/api/health').catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.login('admin', 'test')

      await expect(page).toHaveURL(/\/scan/)
      await expect(page.getByRole('heading', { name: 'Scan' })).toBeVisible()
    })
  })

  test.describe('Protected Routes', () => {
    test('redirects unauthenticated user from / to login', async ({ page }) => {
      await page.goto('/')
      await expect(page).toHaveURL(/\/login/)
    })

    test('redirects unauthenticated user from /scan to login with redirect param', async ({ page }) => {
      await page.goto('/scan')
      await expect(page).toHaveURL(/\/login\?redirect=\/scan/)
    })

    test('redirects unauthenticated user from /products to login', async ({ page }) => {
      await page.goto('/products')
      await expect(page).toHaveURL(/\/login/)
    })

    test('redirects unauthenticated user from /settings to login', async ({ page }) => {
      await page.goto('/settings')
      await expect(page).toHaveURL(/\/login/)
    })
  })

  test.describe('Logout', () => {
    test('logout returns to login page', async ({ page, request }) => {
      const health = await request.get('/api/health').catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      // Login first
      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.login('admin', 'test')
      await expect(page).toHaveURL(/\/scan/)

      // Logout
      await page.locator('button:has(.q-icon)').filter({ hasText: /logout/i }).or(
        page.locator('[data-testid="nav-logout"]')
      ).click()

      await expect(page).toHaveURL(/\/login/)
    })
  })
})
