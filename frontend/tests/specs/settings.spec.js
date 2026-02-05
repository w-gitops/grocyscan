/**
 * Settings Page Tests
 * 
 * Tests for all 5 settings tabs: Grocy, LLM, Lookup, Scanning, UI.
 * Maps to BrowserMCP test cases SET-G01 through SET-U06.
 */
import { test, expect } from '../fixtures/auth.fixture.js'
import { SettingsPage } from '../pages/settings.page.js'

test.describe('Settings Page', () => {
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

    // Navigate to settings
    await page.goto('/settings')
  })

  test.describe('Page Elements', () => {
    test('displays page title', async ({ page }) => {
      await expect(page.getByText('Settings')).toBeVisible()
    })

    test('displays all 5 tabs', async ({ page }) => {
      await expect(page.getByTestId('settings-tab-grocy')).toBeVisible()
      await expect(page.getByTestId('settings-tab-llm')).toBeVisible()
      await expect(page.getByTestId('settings-tab-lookup')).toBeVisible()
      await expect(page.getByTestId('settings-tab-scanning')).toBeVisible()
      await expect(page.getByTestId('settings-tab-ui')).toBeVisible()
    })

    test('Grocy tab is active by default', async ({ page }) => {
      await expect(page.getByTestId('settings-panel-grocy')).toBeVisible()
    })
  })

  test.describe('Grocy Tab', () => {
    // SET-G01: API URL field
    test('displays API URL field', async ({ page }) => {
      await expect(page.getByTestId('grocy-api-url')).toBeVisible()
    })

    // SET-G02: API Key field
    test('displays API Key field', async ({ page }) => {
      await expect(page.getByTestId('grocy-api-key')).toBeVisible()
    })

    // SET-G03: Web URL field
    test('displays Web URL field', async ({ page }) => {
      await expect(page.getByTestId('grocy-web-url')).toBeVisible()
    })

    // SET-G04: Can edit API URL
    test('can edit API URL', async ({ page }) => {
      const apiUrl = page.getByTestId('grocy-api-url')
      await apiUrl.fill('http://grocy.local:9283')
      await expect(apiUrl).toHaveValue('http://grocy.local:9283')
    })

    // SET-G05: Test Connection button
    test('displays Test Connection button', async ({ page }) => {
      await expect(page.getByTestId('grocy-test-connection')).toBeVisible()
    })

    // SET-G06: Test Connection shows status
    test('Test Connection button shows status', async ({ page }) => {
      await page.getByTestId('grocy-test-connection').click()
      
      // Should show some status (success or error)
      await page.waitForTimeout(3000)
      const status = page.getByTestId('grocy-test-status')
      await expect(status).toBeVisible()
    })

    // SET-G07: Save button
    test('displays Save button', async ({ page }) => {
      await expect(page.getByTestId('grocy-save-button')).toBeVisible()
    })
  })

  test.describe('LLM Tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByTestId('settings-tab-llm').click()
    })

    // SET-L01: Switch to LLM tab
    test('LLM panel is visible after clicking tab', async ({ page }) => {
      await expect(page.getByTestId('settings-panel-llm')).toBeVisible()
    })

    // SET-L02: Provider preset dropdown
    test('displays provider preset dropdown', async ({ page }) => {
      await expect(page.getByTestId('llm-provider-preset')).toBeVisible()
    })

    // SET-L03: API URL field
    test('displays API URL field', async ({ page }) => {
      await expect(page.getByTestId('llm-api-url')).toBeVisible()
    })

    // SET-L04: API Key field
    test('displays API Key field', async ({ page }) => {
      await expect(page.getByTestId('llm-api-key')).toBeVisible()
    })

    // SET-L05: Model field
    test('displays Model field', async ({ page }) => {
      await expect(page.getByTestId('llm-model')).toBeVisible()
    })

    // SET-L06: Save button
    test('displays Save button', async ({ page }) => {
      await expect(page.getByTestId('llm-save-button')).toBeVisible()
    })
  })

  test.describe('Lookup Tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByTestId('settings-tab-lookup').click()
    })

    // SET-K01: Switch to Lookup tab
    test('Lookup panel is visible after clicking tab', async ({ page }) => {
      await expect(page.getByTestId('settings-panel-lookup')).toBeVisible()
    })

    // SET-K02: Strategy dropdown
    test('displays strategy dropdown', async ({ page }) => {
      await expect(page.getByTestId('lookup-strategy')).toBeVisible()
    })

    // SET-K03: OpenFoodFacts card
    test('displays OpenFoodFacts card with toggle', async ({ page }) => {
      await expect(page.getByTestId('lookup-openfoodfacts-card')).toBeVisible()
      await expect(page.getByTestId('lookup-openfoodfacts-toggle')).toBeVisible()
    })

    // SET-K04: Toggle OpenFoodFacts
    test('can toggle OpenFoodFacts', async ({ page }) => {
      const toggle = page.getByTestId('lookup-openfoodfacts-toggle')
      const initialState = await toggle.isChecked()
      
      await toggle.click()
      await expect(toggle).toBeChecked({ checked: !initialState })
    })

    // SET-K05: go-upc card
    test('displays go-upc card with toggle', async ({ page }) => {
      await expect(page.getByTestId('lookup-goupc-card')).toBeVisible()
      await expect(page.getByTestId('lookup-goupc-toggle')).toBeVisible()
    })

    // SET-K06: go-upc API key field
    test('displays go-upc API key field', async ({ page }) => {
      await expect(page.getByTestId('lookup-goupc-apikey')).toBeVisible()
    })

    // SET-K07: Test buttons
    test('displays test buttons for providers', async ({ page }) => {
      await expect(page.getByTestId('lookup-test-openfoodfacts')).toBeVisible()
      await expect(page.getByTestId('lookup-test-goupc')).toBeVisible()
    })
  })

  test.describe('Scanning Tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByTestId('settings-tab-scanning').click()
    })

    // SET-S01: Switch to Scanning tab
    test('Scanning panel is visible after clicking tab', async ({ page }) => {
      await expect(page.getByTestId('settings-panel-scanning')).toBeVisible()
    })

    // SET-S02: Auto-add toggle
    test('displays auto-add toggle', async ({ page }) => {
      await expect(page.getByTestId('scanning-auto-add')).toBeVisible()
    })

    // SET-S03: Toggle auto-add
    test('can toggle auto-add', async ({ page }) => {
      const toggle = page.getByTestId('scanning-auto-add')
      const initialState = await toggle.isChecked()
      
      await toggle.click()
      await expect(toggle).toBeChecked({ checked: !initialState })
    })

    // SET-S05: Fuzzy match threshold
    test('displays fuzzy match threshold', async ({ page }) => {
      await expect(page.getByTestId('scanning-fuzzy-threshold')).toBeVisible()
    })

    // SET-S06: Can adjust threshold
    test('can adjust fuzzy threshold', async ({ page }) => {
      const threshold = page.getByTestId('scanning-fuzzy-threshold')
      await threshold.fill('0.85')
      await expect(threshold).toHaveValue('0.85')
    })

    // SET-S07: Default quantity unit
    test('displays default quantity unit', async ({ page }) => {
      await expect(page.getByTestId('scanning-default-quantity-unit')).toBeVisible()
    })
  })

  test.describe('UI Tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByTestId('settings-tab-ui').click()
    })

    // SET-U01: Switch to UI tab
    test('UI panel is visible after clicking tab', async ({ page }) => {
      await expect(page.getByTestId('settings-panel-ui')).toBeVisible()
    })

    // SET-U02: Kiosk mode toggle
    test('displays kiosk mode toggle', async ({ page }) => {
      await expect(page.getByTestId('scanning-kiosk-mode')).toBeVisible()
    })

    // SET-U03: Save button
    test('displays save button', async ({ page }) => {
      await expect(page.getByTestId('ui-save-button')).toBeVisible()
    })
  })

  test.describe('Tab Navigation', () => {
    test('can navigate through all tabs', async ({ page }) => {
      // Start on Grocy
      await expect(page.getByTestId('settings-panel-grocy')).toBeVisible()

      // Go to LLM
      await page.getByTestId('settings-tab-llm').click()
      await expect(page.getByTestId('settings-panel-llm')).toBeVisible()

      // Go to Lookup
      await page.getByTestId('settings-tab-lookup').click()
      await expect(page.getByTestId('settings-panel-lookup')).toBeVisible()

      // Go to Scanning
      await page.getByTestId('settings-tab-scanning').click()
      await expect(page.getByTestId('settings-panel-scanning')).toBeVisible()

      // Go to UI
      await page.getByTestId('settings-tab-ui').click()
      await expect(page.getByTestId('settings-panel-ui')).toBeVisible()

      // Back to Grocy
      await page.getByTestId('settings-tab-grocy').click()
      await expect(page.getByTestId('settings-panel-grocy')).toBeVisible()
    })
  })
})
