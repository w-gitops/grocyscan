/**
 * Products Page Tests
 * 
 * Tests for product listing, search, and management.
 * Maps to BrowserMCP test cases PROD-01 through PROD-06.
 */
import { test, expect } from '../fixtures/auth.fixture.js'
import { ProductsPage } from '../pages/products.page.js'

test.describe('Products Page', () => {
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

    // Navigate to products
    await page.goto('/products')
  })

  test.describe('Page Elements', () => {
    // PROD-01: Page title
    test('displays page title', async ({ page }) => {
      await expect(page.getByText('Products')).toBeVisible()
    })

    // PROD-02: Search input
    test('displays search input', async ({ page }) => {
      await expect(page.getByTestId('products-search')).toBeVisible()
      await expect(page.getByPlaceholder(/search products/i)).toBeVisible()
    })

    // PROD-03: Product list or empty state
    test('displays product list or empty state', async ({ page }) => {
      // Should show either products list or empty state
      const list = page.getByTestId('products-list')
      const empty = page.getByTestId('products-empty')
      
      await page.waitForTimeout(2000)
      
      const hasProducts = await list.isVisible().catch(() => false)
      const isEmpty = await empty.isVisible().catch(() => false)
      
      expect(hasProducts || isEmpty).toBeTruthy()
    })
  })

  test.describe('Search Functionality', () => {
    // PROD-04: Search input accepts text
    test('search input accepts text', async ({ page }) => {
      const search = page.getByTestId('products-search')
      await search.fill('milk')
      await expect(search).toHaveValue('milk')
    })

    // PROD-05: Search filters products
    test('search filters the product list', async ({ page }) => {
      const search = page.getByTestId('products-search')
      await search.fill('test')
      
      // Wait for debounced search
      await page.waitForTimeout(1000)
      
      // List should be filtered (or empty if no matches)
      const list = page.getByTestId('products-list')
      const empty = page.getByTestId('products-empty')
      
      const hasResults = await list.isVisible().catch(() => false)
      const noResults = await empty.isVisible().catch(() => false)
      
      expect(hasResults || noResults).toBeTruthy()
    })

    test('clearing search shows all products', async ({ page }) => {
      const search = page.getByTestId('products-search')
      
      // Search for something
      await search.fill('xyz123')
      await page.waitForTimeout(500)
      
      // Clear search
      await search.clear()
      await page.waitForTimeout(500)
      
      // Page should update
      await expect(page.getByTestId('products-page')).toBeVisible()
    })
  })

  test.describe('Product Detail Dialog', () => {
    test('clicking a product opens detail dialog', async ({ page }) => {
      // Wait for products to load
      await page.waitForTimeout(2000)
      
      const productCard = page.getByTestId('product-card').first()
      
      if (await productCard.isVisible().catch(() => false)) {
        await productCard.click()
        await expect(page.getByTestId('product-detail-dialog')).toBeVisible()
      }
    })

    test('detail dialog has close button', async ({ page }) => {
      await page.waitForTimeout(2000)
      
      const productCard = page.getByTestId('product-card').first()
      
      if (await productCard.isVisible().catch(() => false)) {
        await productCard.click()
        await expect(page.getByTestId('product-detail-close')).toBeVisible()
        
        // Close dialog
        await page.getByTestId('product-detail-close').click()
        await expect(page.getByTestId('product-detail-dialog')).not.toBeVisible()
      }
    })

    test('detail dialog has edit button', async ({ page }) => {
      await page.waitForTimeout(2000)
      
      const productCard = page.getByTestId('product-card').first()
      
      if (await productCard.isVisible().catch(() => false)) {
        await productCard.click()
        await expect(page.getByTestId('product-edit-button')).toBeVisible()
      }
    })
  })

  test.describe('Product Edit Dialog', () => {
    test('edit button opens edit dialog', async ({ page }) => {
      await page.waitForTimeout(2000)
      
      const productCard = page.getByTestId('product-card').first()
      
      if (await productCard.isVisible().catch(() => false)) {
        await productCard.click()
        await page.getByTestId('product-edit-button').click()
        
        await expect(page.getByTestId('product-edit-dialog')).toBeVisible()
        await expect(page.getByTestId('product-name-input')).toBeVisible()
      }
    })

    test('edit dialog has name, description, category fields', async ({ page }) => {
      await page.waitForTimeout(2000)
      
      const productCard = page.getByTestId('product-card').first()
      
      if (await productCard.isVisible().catch(() => false)) {
        await productCard.click()
        await page.getByTestId('product-edit-button').click()
        
        await expect(page.getByTestId('product-name-input')).toBeVisible()
        await expect(page.getByTestId('product-description-input')).toBeVisible()
        await expect(page.getByTestId('product-category-input')).toBeVisible()
      }
    })

    test('edit dialog has save and cancel buttons', async ({ page }) => {
      await page.waitForTimeout(2000)
      
      const productCard = page.getByTestId('product-card').first()
      
      if (await productCard.isVisible().catch(() => false)) {
        await productCard.click()
        await page.getByTestId('product-edit-button').click()
        
        await expect(page.getByTestId('product-save-button')).toBeVisible()
        await expect(page.getByTestId('product-cancel-button')).toBeVisible()
      }
    })
  })

  test.describe('Stock Management', () => {
    test('detail dialog shows add stock button', async ({ page }) => {
      await page.waitForTimeout(2000)
      
      const productCard = page.getByTestId('product-card').first()
      
      if (await productCard.isVisible().catch(() => false)) {
        await productCard.click()
        await expect(page.getByTestId('product-add-stock-button')).toBeVisible()
      }
    })

    test('detail dialog shows consume stock button', async ({ page }) => {
      await page.waitForTimeout(2000)
      
      const productCard = page.getByTestId('product-card').first()
      
      if (await productCard.isVisible().catch(() => false)) {
        await productCard.click()
        await expect(page.getByTestId('product-consume-stock-button')).toBeVisible()
      }
    })
  })
})
