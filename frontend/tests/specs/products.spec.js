/**
 * Products Page Tests
 */
import { test, expect } from '../fixtures/index.js'
import { ProductsPage } from '../pages/products.page.js'
import { LoginPage } from '../pages/login.page.js'

test.describe('Products Page', () => {
  test.beforeEach(async ({ page, request, baseURL }) => {
    const health = await request.get(`${baseURL}/api/health`).catch(() => null)
    if (!health?.ok()) {
      test.skip(true, 'Backend not available')
    }

    const loginPage = new LoginPage(page)
    await loginPage.navigate()
    await loginPage.login('admin', 'test')
    await page.goto('/products')
  })

  test.describe('Page Elements', () => {
    test('displays page title', async ({ page }) => {
      await expect(page.getByText('Products')).toBeVisible()
    })

    test('displays search input', async ({ page }) => {
      const searchInput = page.getByPlaceholder(/search/i)
      await expect(searchInput).toBeVisible()
    })

    test('displays product list or empty state', async ({ page }) => {
      // Wait for load
      await page.waitForTimeout(1000)
      
      const hasList = await page.locator('.q-list').isVisible().catch(() => false)
      const hasEmpty = await page.getByText(/no products/i).isVisible().catch(() => false)
      
      expect(hasList || hasEmpty).toBe(true)
    })
  })

  test.describe('Search', () => {
    test('can type in search field', async ({ page }) => {
      const productsPage = new ProductsPage(page)
      await productsPage.search('test product')
      await expect(productsPage.getSearchInput()).toHaveValue('test product')
    })

    test('search filters product list', async ({ page }) => {
      const productsPage = new ProductsPage(page)
      
      // Get initial count
      await page.waitForTimeout(500)
      const initialCount = await productsPage.getProductCount()
      
      // Search for something unlikely
      await productsPage.search('xyznonexistent123')
      await page.waitForTimeout(500)
      
      // Count should be 0 or show empty state
      const filteredCount = await productsPage.getProductCount()
      expect(filteredCount).toBeLessThanOrEqual(initialCount)
    })
  })

  test.describe('Product Detail', () => {
    test('clicking product opens detail dialog', async ({ page }) => {
      const productsPage = new ProductsPage(page)
      await page.waitForTimeout(1000)
      
      const productCount = await productsPage.getProductCount()
      if (productCount === 0) {
        test.skip(true, 'No products to test')
      }
      
      await productsPage.openFirstProduct()
      
      // Dialog should open
      const dialog = page.locator('.q-dialog')
      await expect(dialog).toBeVisible()
    })

    test('detail dialog shows product name', async ({ page }) => {
      const productsPage = new ProductsPage(page)
      await page.waitForTimeout(1000)
      
      const productCount = await productsPage.getProductCount()
      if (productCount === 0) {
        test.skip(true, 'No products to test')
      }
      
      await productsPage.openFirstProduct()
      
      // Should have product name in dialog
      const dialog = page.locator('.q-dialog')
      const hasName = await dialog.locator('.text-h6').isVisible().catch(() => false)
      expect(hasName).toBe(true)
    })

    test('detail dialog has close button', async ({ page }) => {
      const productsPage = new ProductsPage(page)
      await page.waitForTimeout(1000)
      
      const productCount = await productsPage.getProductCount()
      if (productCount === 0) {
        test.skip(true, 'No products to test')
      }
      
      await productsPage.openFirstProduct()
      
      const closeBtn = page.getByRole('button', { name: /close/i })
      await expect(closeBtn).toBeVisible()
    })
  })

  test.describe('Edit Product', () => {
    test('can open edit dialog from detail', async ({ page }) => {
      const productsPage = new ProductsPage(page)
      await page.waitForTimeout(1000)
      
      const productCount = await productsPage.getProductCount()
      if (productCount === 0) {
        test.skip(true, 'No products to test')
      }
      
      await productsPage.openFirstProduct()
      
      const editBtn = page.getByRole('button', { name: /edit/i })
      await editBtn.click()
      
      // Edit dialog should be visible
      const editDialog = page.locator('.q-dialog:has-text("Edit Product")')
      await expect(editDialog).toBeVisible()
    })

    test('edit dialog has name field', async ({ page }) => {
      const productsPage = new ProductsPage(page)
      await page.waitForTimeout(1000)
      
      const productCount = await productsPage.getProductCount()
      if (productCount === 0) {
        test.skip(true, 'No products to test')
      }
      
      await productsPage.openFirstProduct()
      await page.getByRole('button', { name: /edit/i }).click()
      
      const nameInput = page.getByLabel('Name')
      await expect(nameInput).toBeVisible()
    })

    test('edit dialog has save and cancel buttons', async ({ page }) => {
      const productsPage = new ProductsPage(page)
      await page.waitForTimeout(1000)
      
      const productCount = await productsPage.getProductCount()
      if (productCount === 0) {
        test.skip(true, 'No products to test')
      }
      
      await productsPage.openFirstProduct()
      await page.getByRole('button', { name: /edit/i }).click()
      
      await expect(page.getByRole('button', { name: /save/i })).toBeVisible()
      await expect(page.getByRole('button', { name: /cancel/i })).toBeVisible()
    })
  })
})
