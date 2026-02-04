/**
 * Products Page Object
 */
import { BasePage } from './base.page.js'

export class ProductsPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Page elements
    this.pageContainer = this.getByTestId('products-page')
    this.searchInput = this.getByTestId('products-search')
    this.loadingState = this.getByTestId('products-loading')
    this.emptyState = this.getByTestId('products-empty')
    this.productList = this.getByTestId('products-list')
    
    // Product card
    this.productCard = this.getByTestId('product-card')
    
    // Detail dialog
    this.detailDialog = this.getByTestId('product-detail-dialog')
    this.detailName = this.getByTestId('product-detail-name')
    this.barcodesList = this.getByTestId('product-barcodes-list')
    this.barcodeChip = this.getByTestId('product-barcode-chip')
    
    // Stock adjustment
    this.addQtyInput = this.getByTestId('product-add-qty')
    this.addLocationSelect = this.getByTestId('product-add-location')
    this.addStockBtn = this.getByTestId('product-add-stock-button')
    this.consumeQtyInput = this.getByTestId('product-consume-qty')
    this.consumeStockBtn = this.getByTestId('product-consume-stock-button')
    this.editButton = this.getByTestId('product-edit-button')
    this.detailCloseBtn = this.getByTestId('product-detail-close')
    
    // Edit dialog
    this.editDialog = this.getByTestId('product-edit-dialog')
    this.nameInput = this.getByTestId('product-name-input')
    this.descriptionInput = this.getByTestId('product-description-input')
    this.categoryInput = this.getByTestId('product-category-input')
    this.barcodeInput = this.getByTestId('product-barcode-input')
    this.addBarcodeBtn = this.getByTestId('product-add-barcode-button')
    this.cancelButton = this.getByTestId('product-cancel-button')
    this.saveButton = this.getByTestId('product-save-button')
    
    // Fallbacks
    this.searchInputFallback = page.getByPlaceholder('Search products')
  }

  async goto() {
    await this.page.goto('/products')
  }

  async isOnPage() {
    return this.page.url().includes('/products')
  }

  /**
   * Get search input (with fallback)
   */
  getSearchInput() {
    return this.searchInput.or(this.searchInputFallback)
  }

  /**
   * Search for products
   */
  async search(query) {
    await this.getSearchInput().fill(query)
    await this.page.waitForTimeout(300) // Debounce
  }

  /**
   * Get product count
   */
  async getProductCount() {
    return this.productCard.count()
  }

  /**
   * Click on a product by name
   */
  async openProduct(name) {
    await this.page.locator(`[data-testid="product-card"]:has-text("${name}")`).click()
  }

  /**
   * Click first product in list
   */
  async openFirstProduct() {
    await this.productCard.first().click()
  }

  /**
   * Check if detail dialog is open
   */
  async isDetailDialogOpen() {
    return this.detailDialog.isVisible().catch(() => false)
  }

  /**
   * Close detail dialog
   */
  async closeDetailDialog() {
    await this.detailCloseBtn.click()
  }

  /**
   * Open edit dialog from detail
   */
  async openEditDialog() {
    await this.editButton.click()
  }

  /**
   * Check if edit dialog is open
   */
  async isEditDialogOpen() {
    return this.editDialog.isVisible().catch(() => false)
  }

  /**
   * Fill edit form
   */
  async fillEditForm({ name, description, category }) {
    if (name !== undefined) await this.nameInput.fill(name)
    if (description !== undefined) await this.descriptionInput.fill(description)
    if (category !== undefined) await this.categoryInput.fill(category)
  }

  /**
   * Save edit
   */
  async saveEdit() {
    await this.saveButton.click()
  }

  /**
   * Cancel edit
   */
  async cancelEdit() {
    await this.cancelButton.click()
  }

  /**
   * Add stock to product
   */
  async addStock(quantity) {
    await this.addQtyInput.fill(String(quantity))
    await this.addStockBtn.click()
  }

  /**
   * Consume stock from product
   */
  async consumeStock(quantity) {
    await this.consumeQtyInput.fill(String(quantity))
    await this.consumeStockBtn.click()
  }

  /**
   * Check if loading
   */
  async isLoading() {
    return this.loadingState.isVisible()
  }

  /**
   * Check if empty state shown
   */
  async isEmpty() {
    return this.emptyState.isVisible()
  }
}
