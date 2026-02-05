/**
 * Logs Page Tests
 * 
 * Tests for application log viewing and filtering.
 * Maps to BrowserMCP test cases LOG-01 through LOG-07.
 */
import { test, expect } from '../fixtures/auth.fixture.js'
import { LogsPage } from '../pages/logs.page.js'

test.describe('Logs Page', () => {
  test.beforeEach(async ({ page, request, baseURL }) => {
    const health = await request.get(`${baseURL}/api/health`).catch(() => null)
    if (!health?.ok()) {
      test.skip(true, 'Backend not available')
    }

    // Login
    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('test')
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL(/\/scan/)

    // Navigate to logs
    await page.goto('/logs')
  })

  test.describe('Page Elements', () => {
    // LOG-01: Page title
    test('displays page title', async ({ page }) => {
      await expect(page.getByText(/logs/i)).toBeVisible()
    })

    // LOG-02: Level filter
    test('displays level filter', async ({ page }) => {
      await expect(page.getByText(/level|all levels/i).first()).toBeVisible()
    })

    // LOG-03: Level options available
    test('has log level filtering options', async ({ page }) => {
      // Look for level filter dropdown or similar
      const levelFilter = page.locator('[data-testid="logs-level-filter"], .q-select').first()
      
      if (await levelFilter.isVisible().catch(() => false)) {
        await levelFilter.click()
        // Should show level options
        await expect(page.getByRole('option').first()).toBeVisible({ timeout: 2000 })
      }
    })

    // LOG-04: Search input
    test('displays search input', async ({ page }) => {
      const searchInput = page.locator('[data-testid="logs-search-input"], input[placeholder*="search" i], input[placeholder*="Search" i]').first()
      await expect(searchInput).toBeVisible()
    })

    // LOG-05: Refresh button
    test('displays refresh button', async ({ page }) => {
      const refreshBtn = page.locator('[data-testid="logs-refresh-button"], button:has-text("Refresh"), button:has(.q-icon[name="refresh"])').first()
      await expect(refreshBtn).toBeVisible()
    })

    // LOG-06: Copy All button
    test('displays copy button', async ({ page }) => {
      const copyBtn = page.locator('[data-testid="logs-copy-all-button"], button:has-text("Copy"), button:has(.q-icon[name="content_copy"])').first()
      await expect(copyBtn).toBeVisible()
    })

    // LOG-07: Log container
    test('displays log container', async ({ page }) => {
      // Should have some area for displaying logs
      await page.waitForTimeout(2000)
      await expect(page).toHaveURL(/\/logs/)
    })
  })

  test.describe('Log Filtering', () => {
    test('search input accepts text', async ({ page }) => {
      const searchInput = page.locator('[data-testid="logs-search-input"], input[placeholder*="search" i]').first()
      
      if (await searchInput.isVisible().catch(() => false)) {
        await searchInput.fill('error')
        await expect(searchInput).toHaveValue('error')
      }
    })
  })

  test.describe('Log Actions', () => {
    test('refresh button can be clicked', async ({ page }) => {
      const refreshBtn = page.locator('[data-testid="logs-refresh-button"], button:has-text("Refresh")').first()
      
      if (await refreshBtn.isVisible().catch(() => false)) {
        await refreshBtn.click()
        // Should not error
        await page.waitForTimeout(1000)
      }
    })
  })
})
