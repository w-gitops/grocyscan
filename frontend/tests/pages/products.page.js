/**
 * Products Page Object
 * 
 * Encapsulates all interactions with the products list and detail pages.
 */
import { BasePage } from './base.page.js'

export class ProductsPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Search and filter
    this.searchInput = page.getByTestId('products-search')
    this.categoryFilter = page.getByTestId('products-category-filter')
    this.addButton = page.getByTestId('products-add-button')
    
    // Product list
    this.productList = page.getByTestId('products-list')
    this.productCards = page.getByTestId('product-card')
    this.emptyState = page.getByText(/no products/i)
    this.loadingIndicator = page.locator('.q-spinner')
    
    // Product detail dialog
    this.detailDialog = page.getByTestId('product-detail-dialog')
    this.editButton = page.getByTestId('product-edit-button')
    this.deleteButton = page.getByTestId('product-delete-button')
    
    // Product edit dialog
    this.editDialog = page.getByTestId('product-edit-dialog')
    this.nameInput = page.getByTestId('product-name-input')
    this.descriptionInput = page.getByTestId('product-description-input')
    this.categoryInput = page.getByTestId('product-category-input')
    this.saveButton = page.getByTestId('product-save-button')
    this.cancelButton = page.getByTestId('product-cancel-button')
    
    // Barcode management
    this.barcodesList = page.getByTestId('product-barcodes-list')
    this.addBarcodeButton = page.getByTestId('product-add-barcode-button')
    this.barcodeInput = page.getByTestId('product-barcode-input')
    
    // Stock management
    this.addStockButton = page.getByTestId('product-add-stock-button')
    this.consumeStockButton = page.getByTestId('product-consume-stock-button')
    
    // Fallback selectors
    this.searchInputFallback = page.getByPlaceholder(/search/i)
    this.addButtonFallback = page.getByRole('button', { name: /add product/i })
    this.pageTitle = page.getByRole('heading', { name: 'Products' })
  }

  async goto() {
    await this.page.goto('/products')
  }

  async isOnPage() {
    return this.page.url().includes('/products')
  }

  async waitForLoad() {
    await this.pageTitle.waitFor({ state: 'visible' })
    // Wait for either products to load or empty state
    await Promise.race([
      this.productList.waitFor({ state: 'visible' }).catch(() => {}),
      this.emptyState.waitFor({ state: 'visible' }).catch(() => {}),
      this.page.waitForTimeout(3000)
    ])
  }

  /**
   * Search for products by name
   * @param {string} query 
   */
  async search(query) {
    const input = await this.searchInput.isVisible().catch(() => false)
      ? this.searchInput
      : this.searchInputFallback
    await input.fill(query)
    // Wait for debounced search
    await this.page.waitForTimeout(500)
  }

  /**
   * Clear search input
   */
  async clearSearch() {
    const input = await this.searchInput.isVisible().catch(() => false)
      ? this.searchInput
      : this.searchInputFallback
    await input.clear()
  }

  /**
   * Filter by category
   * @param {string} category 
   */
  async filterByCategory(category) {
    await this.categoryFilter.click()
    await this.page.getByRole('option', { name: category }).click()
  }

  /**
   * Get count of visible products
   */
  async getProductCount() {
    const cards = this.page.locator('[data-testid="product-card"], .product-card, .q-card')
    return await cards.count()
  }

  /**
   * Click on a product card by name
   * @param {string} productName 
   */
  async clickProduct(productName) {
    await this.page.getByText(productName).first().click()
  }

  /**
   * Open add product dialog
   */
  async openAddDialog() {
    const btn = await this.addButton.isVisible().catch(() => false)
      ? this.addButton
      : this.addButtonFallback
    await btn.click()
  }

  /**
   * Fill product form in edit dialog
   * @param {Object} product 
   * @param {string} product.name
   * @param {string} [product.description]
   * @param {string} [product.category]
   */
  async fillProductForm({ name, description, category }) {
    if (name) {
      const nameField = await this.nameInput.isVisible().catch(() => false)
        ? this.nameInput
        : this.page.getByLabel(/name/i).first()
      await nameField.fill(name)
    }
    if (description) {
      const descField = await this.descriptionInput.isVisible().catch(() => false)
        ? this.descriptionInput
        : this.page.getByLabel(/description/i)
      await descField.fill(description)
    }
    if (category) {
      const catField = await this.categoryInput.isVisible().catch(() => false)
        ? this.categoryInput
        : this.page.getByLabel(/category/i)
      await catField.fill(category)
    }
  }

  /**
   * Save product form
   */
  async saveProduct() {
    const btn = await this.saveButton.isVisible().catch(() => false)
      ? this.saveButton
      : this.page.getByRole('button', { name: /save/i })
    await btn.click()
  }

  /**
   * Cancel product form
   */
  async cancelEdit() {
    const btn = await this.cancelButton.isVisible().catch(() => false)
      ? this.cancelButton
      : this.page.getByRole('button', { name: /cancel/i })
    await btn.click()
  }

  /**
   * Check if detail dialog is open
   */
  async isDetailDialogOpen() {
    return await this.detailDialog.isVisible().catch(() => false) ||
           await this.page.getByRole('dialog').isVisible()
  }

  /**
   * Close detail dialog
   */
  async closeDetailDialog() {
    await this.page.getByRole('button', { name: /close|×/i }).click()
  }

  /**
   * Open edit mode from detail dialog
   */
  async openEditMode() {
    const btn = await this.editButton.isVisible().catch(() => false)
      ? this.editButton
      : this.page.getByRole('button', { name: /edit/i })
    await btn.click()
  }

  /**
   * Delete product from detail dialog
   */
  async deleteProduct() {
    const btn = await this.deleteButton.isVisible().catch(() => false)
      ? this.deleteButton
      : this.page.getByRole('button', { name: /delete/i })
    await btn.click()
    // Confirm deletion if dialog appears
    const confirmBtn = this.page.getByRole('button', { name: /confirm|yes|delete/i })
    if (await confirmBtn.isVisible()) {
      await confirmBtn.click()
    }
  }

  /**
   * Add a barcode to the current product
   * @param {string} barcode 
   */
  async addBarcode(barcode) {
    await this.addBarcodeButton.click()
    await this.barcodeInput.fill(barcode)
    await this.page.getByRole('button', { name: /add|save/i }).click()
  }
}
