/**
 * Authentication Tests
 * 
 * Tests for login flow, session management, and protected routes.
 * Maps to BrowserMCP test cases AUTH-01 through AUTH-07.
 */
import { test, expect } from '@playwright/test'
import { LoginPage } from '../pages/login.page.js'

test.describe('Authentication', () => {
  test.describe('Login Page', () => {
    // AUTH-01: Login page loads with all elements
    test('displays login form with all required elements', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.goto()
      await loginPage.waitForLoad()

      // Check title and branding
      await expect(page.getByText('Sign in to continue')).toBeVisible()
      
      // Check form elements
      await expect(page.getByLabel('Username')).toBeVisible()
      await expect(page.getByLabel('Password')).toBeVisible()
      await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible()
    })

    // AUTH-02: Empty form validation
    test('shows validation when submitting empty form', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.goto()
      await loginPage.waitForLoad()

      // Click submit without entering credentials
      await page.getByRole('button', { name: /sign in/i }).click()

      // Should show validation errors (Quasar shows "Required" messages)
      await expect(page.getByText('Required')).toBeVisible()
    })

    // AUTH-03: Username input accepts text
    test('accepts username input', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.goto()
      await loginPage.waitForLoad()

      await page.getByLabel('Username').fill('testuser')
      await expect(page.getByLabel('Username')).toHaveValue('testuser')
    })

    // AUTH-04: Password input accepts text and masks it
    test('accepts password input and masks characters', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.goto()
      await loginPage.waitForLoad()

      const passwordInput = page.getByLabel('Password')
      await passwordInput.fill('password123')
      
      // Check input type is password (masked)
      await expect(passwordInput).toHaveAttribute('type', 'password')
    })

    // AUTH-05: Password visibility toggle
    test('toggles password visibility', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.goto()
      await loginPage.waitForLoad()

      const passwordInput = page.getByLabel('Password')
      await passwordInput.fill('password123')

      // Initially masked
      await expect(passwordInput).toHaveAttribute('type', 'password')

      // Click toggle button
      await page.getByTestId('login-password-toggle').click()

      // Now visible
      await expect(passwordInput).toHaveAttribute('type', 'text')

      // Toggle back
      await page.getByTestId('login-password-toggle').click()
      await expect(passwordInput).toHaveAttribute('type', 'password')
    })

    // AUTH-06: Invalid credentials show error
    test('shows error for invalid credentials', async ({ page, request, baseURL }) => {
      // Check if backend is available
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      const loginPage = new LoginPage(page)
      await loginPage.goto()
      await loginPage.waitForLoad()

      await loginPage.login('wronguser', 'wrongpassword')

      // Should show error message
      await expect(page.getByTestId('login-error')).toBeVisible({ timeout: 5000 })
    })

    // AUTH-07: Successful login redirects to scan page
    test('redirects to scan page on successful login', async ({ page, request, baseURL }) => {
      // Check if backend is available
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      const loginPage = new LoginPage(page)
      await loginPage.goto()
      await loginPage.waitForLoad()

      await loginPage.loginAndWaitForRedirect('admin', 'test', /\/scan/)

      // Verify we're on the scan page
      await expect(page.getByRole('heading', { name: 'Scan' })).toBeVisible()
    })
  })

  test.describe('Protected Routes', () => {
    // Unauthenticated access to root redirects to login
    test('redirects unauthenticated user from / to login', async ({ page }) => {
      await page.goto('/')
      await expect(page).toHaveURL(/\/login/)
      await expect(page.getByText('Sign in to continue')).toBeVisible()
    })

    // Unauthenticated access to /scan includes redirect param
    test('preserves redirect param when redirecting to login', async ({ page }) => {
      await page.goto('/scan')
      await expect(page).toHaveURL(/\/login\?redirect=\/scan/)
    })

    // Protected pages redirect to login
    test.describe('all protected pages redirect to login', () => {
      const protectedRoutes = [
        '/products',
        '/inventory',
        '/locations',
        '/jobs',
        '/logs',
        '/settings'
      ]

      for (const route of protectedRoutes) {
        test(`${route} redirects to login`, async ({ page }) => {
          await page.goto(route)
          await expect(page).toHaveURL(/\/login/)
        })
      }
    })
  })

  test.describe('Session Management', () => {
    // Logout redirects to login
    test('logout redirects to login page', async ({ page, request, baseURL }) => {
      // Check if backend is available
      const health = await request.get(`${baseURL}/api/health`).catch(() => null)
      if (!health?.ok()) {
        test.skip(true, 'Backend not available')
      }

      const loginPage = new LoginPage(page)
      await loginPage.goto()
      await loginPage.loginAndWaitForRedirect('admin', 'test', /\/scan/)

      // Click logout
      await page.getByTestId('logout-button').click()

      // Should be on login page
      await expect(page).toHaveURL(/\/login/)
    })
  })
})
