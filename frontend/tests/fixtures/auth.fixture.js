/**
 * Authentication fixtures for Playwright tests
 * 
 * Provides pre-authenticated page contexts and storage state management
 * for tests that require a logged-in user.
 */
import { test as base, expect } from '@playwright/test'

/**
 * Extended test with authentication fixtures
 */
export const test = base.extend({
  /**
   * Authenticated page fixture - logs in via API before test
   * Use when you need a fresh authenticated session for each test
   */
  authenticatedPage: async ({ page, request, baseURL }, use) => {
    // Login via API to get session cookie
    const loginResponse = await request.post(`${baseURL}/api/auth/login`, {
      data: { username: 'admin', password: 'test' },
      headers: { 'Content-Type': 'application/json' }
    })
    
    if (!loginResponse.ok()) {
      // If backend not available, skip gracefully
      test.skip(true, 'Backend not available for authentication')
    }
    
    await use(page)
  },

  /**
   * Storage state fixture - creates reusable auth state
   * Use with test.use({ storageState }) for faster test setup
   */
  authStorageState: async ({ browser, baseURL }, use) => {
    const context = await browser.newContext()
    const page = await context.newPage()
    
    await page.goto(`${baseURL}/login`)
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('test')
    await page.getByRole('button', { name: /sign in/i }).click()
    
    // Wait for successful redirect to scan page
    await page.waitForURL(/\/scan/, { timeout: 10000 })
    
    // Save storage state
    const state = await context.storageState()
    await context.close()
    
    await use(state)
  },

  /**
   * Pre-authenticated context - creates context with saved auth
   * More efficient than authenticatedPage for multiple tests
   */
  authedContext: async ({ browser, authStorageState }, use) => {
    const context = await browser.newContext({ storageState: authStorageState })
    await use(context)
    await context.close()
  },

  /**
   * Pre-authenticated page from authed context
   */
  authedPage: async ({ authedContext }, use) => {
    const page = await authedContext.newPage()
    await use(page)
    await page.close()
  }
})

// Re-export expect for convenience
export { expect }

/**
 * Test credentials - matches CI environment
 */
export const TEST_CREDENTIALS = {
  username: 'admin',
  password: 'test'
}

/**
 * Helper to check if backend is available
 */
export async function isBackendAvailable(request, baseURL) {
  try {
    const health = await request.get(`${baseURL}/api/health`)
    return health.ok()
  } catch {
    return false
  }
}

/**
 * Helper to skip test if backend unavailable
 */
export async function skipIfNoBackend(request, baseURL, testInfo) {
  const available = await isBackendAvailable(request, baseURL)
  if (!available) {
    testInfo.skip(true, 'Backend not available')
  }
  return available
}
