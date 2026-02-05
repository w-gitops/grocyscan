/**
 * Locations Page Tests
 */
import { test, expect } from '../fixtures/index.js'
import { LocationsPage } from '../pages/locations.page.js'
import { LoginPage } from '../pages/login.page.js'

test.describe('Locations Page', () => {
  test.beforeEach(async ({ page, request, baseURL }) => {
    const health = await request.get(`${baseURL}/api/health`).catch(() => null)
    if (!health?.ok()) {
      test.skip(true, 'Backend not available')
    }

    const loginPage = new LoginPage(page)
    await loginPage.navigate()
    await loginPage.login('admin', 'test')
    await page.goto('/locations')
  })

  test.describe('Page Elements', () => {
    test('displays page title', async ({ page }) => {
      await expect(page.getByText('Locations')).toBeVisible()
    })

    test('displays add location button', async ({ page }) => {
      const addBtn = page.getByRole('button', { name: /add location/i })
      await expect(addBtn).toBeVisible()
    })

    test('displays location list or empty state', async ({ page }) => {
      await page.waitForTimeout(1000)
      
      const hasList = await page.locator('.q-list').isVisible().catch(() => false)
      const hasEmpty = await page.getByText(/no locations/i).isVisible().catch(() => false)
      
      expect(hasList || hasEmpty).toBe(true)
    })
  })

  test.describe('Add Location Dialog', () => {
    test('can open add location dialog', async ({ page }) => {
      const locationsPage = new LocationsPage(page)
      await locationsPage.openAddDialog()
      
      await expect(await locationsPage.isDialogOpen()).toBe(true)
    })

    test('add dialog has name input', async ({ page }) => {
      const locationsPage = new LocationsPage(page)
      await locationsPage.openAddDialog()
      
      const nameInput = page.getByLabel('Name')
      await expect(nameInput).toBeVisible()
    })

    test('add dialog has type selector', async ({ page }) => {
      const locationsPage = new LocationsPage(page)
      await locationsPage.openAddDialog()
      
      const typeSelect = page.getByLabel('Type')
      await expect(typeSelect).toBeVisible()
    })

    test('add dialog has freezer toggle', async ({ page }) => {
      const locationsPage = new LocationsPage(page)
      await locationsPage.openAddDialog()
      
      const freezerToggle = page.getByText(/is freezer/i)
      await expect(freezerToggle).toBeVisible()
    })

    test('add dialog has save button', async ({ page }) => {
      const locationsPage = new LocationsPage(page)
      await locationsPage.openAddDialog()
      
      const saveBtn = page.getByRole('button', { name: /add|save/i }).last()
      await expect(saveBtn).toBeVisible()
    })

    test('add dialog has cancel button', async ({ page }) => {
      const locationsPage = new LocationsPage(page)
      await locationsPage.openAddDialog()
      
      const cancelBtn = page.getByRole('button', { name: /cancel/i })
      await expect(cancelBtn).toBeVisible()
    })
  })

  test.describe('Location Creation', () => {
    test('can fill location form', async ({ page }) => {
      const locationsPage = new LocationsPage(page)
      await locationsPage.openAddDialog()
      
      await page.getByLabel('Name').fill('Test Location')
      await expect(page.getByLabel('Name')).toHaveValue('Test Location')
    })

    test('can create new location', async ({ page }) => {
      const locationsPage = new LocationsPage(page)
      const testName = `Test Location ${Date.now()}`
      
      await locationsPage.openAddDialog()
      await page.getByLabel('Name').fill(testName)
      await page.getByRole('button', { name: /add|save/i }).last().click()
      
      // Wait for dialog to close
      await page.waitForTimeout(1000)
      
      // Location should appear in list
      const locationText = page.getByText(testName)
      const isVisible = await locationText.isVisible().catch(() => false)
      expect(isVisible).toBe(true)
    })
  })

  test.describe('Location Actions', () => {
    test('location row has edit button', async ({ page }) => {
      await page.waitForTimeout(1000)
      
      const locationRow = page.locator('[data-testid^="location-row-"]').first()
      const hasRow = await locationRow.isVisible().catch(() => false)
      
      if (!hasRow) {
        test.skip(true, 'No locations to test')
      }
      
      const editBtn = locationRow.locator('[data-testid="location-edit-btn"]')
      await expect(editBtn).toBeVisible()
    })

    test('location row has delete button', async ({ page }) => {
      await page.waitForTimeout(1000)
      
      const locationRow = page.locator('[data-testid^="location-row-"]').first()
      const hasRow = await locationRow.isVisible().catch(() => false)
      
      if (!hasRow) {
        test.skip(true, 'No locations to test')
      }
      
      const deleteBtn = locationRow.locator('[data-testid="location-delete-btn"]')
      await expect(deleteBtn).toBeVisible()
    })
  })
})
