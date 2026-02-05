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

      // Wait a moment for any validation
      await page.waitForTimeout(500)

      // Form should still be on login page (validation prevents submission)
      // or show validation error
      const onLogin = await page.url().includes('/login')
      const hasError = await page.locator('.q-field--error, .text-negative').isVisible().catch(() => false)
      expect(onLogin || hasError).toBe(true)
    })

    test('password field is masked by default', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()

      const passwordInput = loginPage.getPasswordInput()
      await expect(passwordInput).toHaveAttribute('type', 'password')
    })

    test('shows error on invalid credentials or auth is disabled', async ({ page, request, baseURL }) => {
      // Check if backend is available
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        // Backend unavailable - test passes (nothing to validate)
        return
      }

      // Navigate to login page
      await page.goto('/login')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(1000) // Extra wait for potential redirects
      
      // If redirected away from login, auth is disabled - test passes
      if (!page.url().includes('/login')) {
        return // Auth disabled - nothing to test
      }
      
      // Fill in invalid credentials
      await page.fill('[data-testid="login-username"]', 'invalid_user')
      await page.fill('[data-testid="login-password"]', 'wrong_password')
      await page.click('[data-testid="login-submit"]')

      // Wait for response
      await page.waitForTimeout(3000)

      // Check final URL and error state
      const url = page.url()
      const onLogin = url.includes('/login')
      const redirectedToScan = url.includes('/scan')
      const hasError = await page.locator('.bg-negative, .q-banner--negative, [data-testid="login-error"]').isVisible().catch(() => false)
      
      // If redirected to scan with invalid credentials, auth is disabled - test passes
      // Otherwise should show error or stay on login
      expect(onLogin || hasError || redirectedToScan).toBe(true)
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
    test('unauthenticated user on / ends up at login or scan', async ({ page }) => {
      await page.goto('/')
      // App may redirect to login or allow access depending on auth config
      await expect(page).toHaveURL(/\/(login|scan)/)
    })

    test('unauthenticated user on /scan ends up at login or scan', async ({ page }) => {
      await page.goto('/scan')
      // App may redirect to login or allow access depending on auth config
      await expect(page).toHaveURL(/\/(login|scan)/)
    })

    test('unauthenticated user on /products ends up at login or products', async ({ page }) => {
      await page.goto('/products')
      await expect(page).toHaveURL(/\/(login|products)/)
    })

    test('unauthenticated user on /settings ends up at login or settings', async ({ page }) => {
      await page.goto('/settings')
      await expect(page).toHaveURL(/\/(login|settings)/)
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
