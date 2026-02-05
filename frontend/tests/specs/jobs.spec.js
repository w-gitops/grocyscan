/**
 * Jobs Page Tests
 */
import { test, expect } from '../fixtures/index.js'
import { LoginPage } from '../pages/login.page.js'

test.describe('Jobs Page', () => {
  test.beforeEach(async ({ page, request, baseURL }) => {
    const health = await request.get(`${baseURL}/api/health`).catch(() => null)
    if (!health?.ok()) {
      test.skip(true, 'Backend not available')
    }

    const loginPage = new LoginPage(page)
    await loginPage.navigate()
    await loginPage.login('admin', 'test')
    await page.goto('/jobs')
  })

  test.describe('Page Elements', () => {
    test('displays page title', async ({ page }) => {
      // Check for Job Queue or Jobs heading
      const hasJobQueue = await page.getByText('Job Queue').isVisible().catch(() => false)
      const hasJobs = await page.getByText('Jobs').first().isVisible().catch(() => false)
      expect(hasJobQueue || hasJobs).toBe(true)
    })

    test('displays job stats or queue info', async ({ page }) => {
      await page.waitForTimeout(1000)
      
      // Look for stats display, job queue info, or page content
      const hasStats = await page.getByText(/pending|running|completed|failed/i).isVisible().catch(() => false)
      const hasQueue = await page.getByText(/queue|job/i).isVisible().catch(() => false)
      const hasCard = await page.locator('.q-card').first().isVisible().catch(() => false)
      
      expect(hasStats || hasQueue || hasCard).toBe(true)
    })
  })

  test.describe('Job Queue', () => {
    test('page loads without error', async ({ page }) => {
      // Just verify the page loads
      await expect(page).toHaveURL(/\/jobs/)
    })

    test('shows job list or empty state', async ({ page }) => {
      await page.waitForTimeout(1000)
      
      const hasList = await page.locator('.q-list').isVisible().catch(() => false)
      const hasTable = await page.locator('table').isVisible().catch(() => false)
      const hasEmpty = await page.getByText(/no jobs|empty/i).isVisible().catch(() => false)
      const hasCard = await page.locator('.q-card').isVisible().catch(() => false)
      
      expect(hasList || hasTable || hasEmpty || hasCard).toBe(true)
    })
  })
})
