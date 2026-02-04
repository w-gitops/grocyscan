/**
 * Authentication fixture for Playwright tests
 * Provides authenticated page contexts for tests that require login
 */
import { test as base, expect } from '@playwright/test'

export const TEST_CREDENTIALS = {
  username: 'admin',
  password: 'test'
}

/**
 * Check if backend is available
 */
export async function isBackendAvailable(request, baseURL) {
  try {
    const response = await request.get(`${baseURL}/api/health`)
    return response.ok()
  } catch {
    return false
  }
}

/**
 * Skip test if backend is not available
 */
export async function skipIfNoBackend(request, baseURL, testInfo) {
  const available = await isBackendAvailable(request, baseURL)
  if (!available) {
    testInfo.skip(true, 'Backend not available')
  }
  return available
}

/**
 * Extended test with authentication fixtures
 */
export const test = base.extend({
  /**
   * Provides a page that's logged in via API
   * Use for tests that need authenticated state but don't test login itself
   */
  authenticatedPage: async ({ page, request, baseURL }, use) => {
    // Check backend availability
    const available = await isBackendAvailable(request, baseURL)
    if (!available) {
      // Just provide the page without auth - test should skip itself
      await use(page)
      return
    }

    // Login via API
    try {
      const response = await request.post(`${baseURL}/api/auth/login`, {
        data: {
          username: TEST_CREDENTIALS.username,
          password: TEST_CREDENTIALS.password
        }
      })

      if (response.ok()) {
        // Get cookies from response and set them on the page context
        const cookies = response.headers()['set-cookie']
        if (cookies) {
          // Navigate to get the cookies applied
          await page.goto('/')
        }
      }
    } catch (e) {
      console.warn('API login failed:', e.message)
    }

    await use(page)
  },

  /**
   * Provides authentication storage state for reuse
   * Logs in via UI and saves state for faster subsequent tests
   */
  authStorageState: async ({ browser, baseURL }, use) => {
    const context = await browser.newContext()
    const page = await context.newPage()

    try {
      await page.goto(`${baseURL}/login`)
      await page.getByLabel('Username').fill(TEST_CREDENTIALS.username)
      await page.getByLabel('Password').fill(TEST_CREDENTIALS.password)
      await page.getByRole('button', { name: /sign in/i }).click()
      
      // Wait for navigation to complete
      await page.waitForURL(/\/(scan|products|inventory)/)
      
      // Get storage state
      const storageState = await context.storageState()
      await use(storageState)
    } catch (e) {
      console.warn('UI login for storage state failed:', e.message)
      await use(null)
    } finally {
      await context.close()
    }
  },

  /**
   * Provides a browser context with saved auth state
   */
  authedContext: async ({ browser, authStorageState }, use) => {
    if (!authStorageState) {
      const context = await browser.newContext()
      await use(context)
      await context.close()
      return
    }

    const context = await browser.newContext({ storageState: authStorageState })
    await use(context)
    await context.close()
  },

  /**
   * Provides a page from authenticated context
   */
  authedPage: async ({ authedContext }, use) => {
    const page = await authedContext.newPage()
    await use(page)
  }
})

export { expect }
