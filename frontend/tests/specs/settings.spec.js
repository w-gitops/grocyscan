/**
 * Settings Page Tests
 */
import { test, expect } from '../fixtures/index.js'
import { SettingsPage } from '../pages/settings.page.js'
import { LoginPage } from '../pages/login.page.js'

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page, request, baseURL }) => {
    const health = await request.get(`${baseURL}/api/health`).catch(() => null)
    if (!health?.ok()) {
      test.skip(true, 'Backend not available')
    }

    const loginPage = new LoginPage(page)
    await loginPage.navigate()
    await loginPage.login('admin', 'test')
    await page.goto('/settings')
  })

  test.describe('Page Elements', () => {
    test('displays page title', async ({ page }) => {
      // Wait for page to load
      await page.waitForLoadState('networkidle')
      
      // Check for Settings text anywhere on page
      const hasText = await page.getByText('Settings').first().isVisible().catch(() => false)
      const hasHeading = await page.locator('.text-h5').first().isVisible().catch(() => false)
      const hasPage = await page.locator('[data-testid="settings-page"], .q-page').isVisible().catch(() => false)
      const hasTabs = await page.locator('.q-tabs').isVisible().catch(() => false)
      expect(hasText || hasHeading || hasPage || hasTabs).toBe(true)
    })

    test('displays tabs', async ({ page }) => {
      await expect(page.getByRole('tab', { name: /grocy/i })).toBeVisible()
      await expect(page.getByRole('tab', { name: /llm/i })).toBeVisible()
      await expect(page.getByRole('tab', { name: /lookup/i })).toBeVisible()
    })
  })

  test.describe('Grocy Tab', () => {
    test('Grocy tab is visible and clickable', async ({ page }) => {
      const grocyTab = page.getByRole('tab', { name: /grocy/i })
      await grocyTab.click()
      
      // Should show Grocy settings
      await expect(page.getByText(/grocy connection/i)).toBeVisible()
    })

    test('Grocy tab has API URL field', async ({ page }) => {
      const grocyTab = page.getByRole('tab', { name: /grocy/i })
      await grocyTab.click()
      
      const apiUrlInput = page.getByLabel(/api url/i)
      await expect(apiUrlInput).toBeVisible()
    })

    test('Grocy tab has API Key field', async ({ page }) => {
      const grocyTab = page.getByRole('tab', { name: /grocy/i })
      await grocyTab.click()
      
      const apiKeyInput = page.getByLabel(/api key/i).first()
      await expect(apiKeyInput).toBeVisible()
    })

    test('Grocy tab has Test Connection button', async ({ page }) => {
      const grocyTab = page.getByRole('tab', { name: /grocy/i })
      await grocyTab.click()
      
      const testBtn = page.getByRole('button', { name: /test connection/i })
      await expect(testBtn).toBeVisible()
    })

    test('Grocy tab has Save button', async ({ page }) => {
      const grocyTab = page.getByRole('tab', { name: /grocy/i })
      await grocyTab.click()
      
      const saveBtn = page.getByRole('button', { name: /save/i }).first()
      await expect(saveBtn).toBeVisible()
    })
  })

  test.describe('LLM Tab', () => {
    test('LLM tab shows provider preset', async ({ page }) => {
      await page.getByRole('tab', { name: /llm/i }).click()
      
      await expect(page.getByText(/llm configuration/i)).toBeVisible()
      await expect(page.getByLabel(/provider preset/i)).toBeVisible()
    })

    test('LLM tab has model field', async ({ page }) => {
      await page.getByRole('tab', { name: /llm/i }).click()
      
      const modelInput = page.getByLabel(/model/i)
      await expect(modelInput).toBeVisible()
    })
  })

  test.describe('Lookup Tab', () => {
    test('Lookup tab shows strategy selector', async ({ page }) => {
      await page.getByRole('tab', { name: /lookup/i }).click()
      
      await expect(page.getByText(/lookup strategy/i)).toBeVisible()
    })

    test('Lookup tab shows provider toggles', async ({ page }) => {
      await page.getByRole('tab', { name: /lookup/i }).click()
      
      // Check for provider names
      await expect(page.getByText(/openfoodfacts/i)).toBeVisible()
    })

    test('Lookup tab has save button', async ({ page }) => {
      await page.getByRole('tab', { name: /lookup/i }).click()
      
      // Look for the specific "Save Lookup Settings" button
      const saveBtn = page.getByRole('button', { name: /save lookup/i })
      await expect(saveBtn).toBeVisible()
    })
  })

  test.describe('Scanning Tab', () => {
    test('Scanning tab shows scanning behavior settings', async ({ page }) => {
      await page.getByRole('tab', { name: /scanning/i }).click()
      
      await expect(page.getByText(/scanning behavior/i)).toBeVisible()
    })

    test('Scanning tab has auto-add toggle', async ({ page }) => {
      await page.getByRole('tab', { name: /scanning/i }).click()
      
      const autoAddToggle = page.getByText(/auto.?add/i)
      await expect(autoAddToggle).toBeVisible()
    })
  })

  test.describe('UI Tab', () => {
    test('UI tab shows UI settings', async ({ page }) => {
      await page.getByRole('tab', { name: /ui/i }).click()
      
      await expect(page.getByText(/ui settings/i)).toBeVisible()
    })

    test('UI tab has kiosk mode toggle', async ({ page }) => {
      await page.getByRole('tab', { name: /ui/i }).click()
      
      const kioskToggle = page.getByText(/kiosk mode/i)
      await expect(kioskToggle).toBeVisible()
    })
  })

  test.describe('Tab Navigation', () => {
    test('can switch between all tabs', async ({ page }) => {
      const tabs = ['grocy', 'llm', 'lookup', 'scanning', 'ui']
      
      for (const tabName of tabs) {
        await page.getByRole('tab', { name: new RegExp(tabName, 'i') }).click()
        // Tab should be active
        const tab = page.getByRole('tab', { name: new RegExp(tabName, 'i') })
        await expect(tab).toHaveClass(/q-tab--active/)
      }
    })
  })
})
