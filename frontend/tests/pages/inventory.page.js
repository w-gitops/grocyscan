/**
 * Inventory Page Object
 */
import { BasePage } from './base.page.js'

export class InventoryPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Page elements
    this.pageContainer = this.getByTestId('inventory-page')
    this.table = this.getByTestId('inventory-table')
    this.loadingState = this.getByTestId('inventory-loading')
    this.emptyState = this.getByTestId('inventory-empty')
    
    // Filters
    this.searchInput = this.getByTestId('inventory-search')
    this.locationFilter = this.getByTestId('inventory-location-filter')
    this.expiringFilter = this.getByTestId('inventory-expiring-filter')
    
    // Pagination
    this.pagination = this.getByTestId('inventory-pagination')
    this.prevPageBtn = this.getByTestId('inventory-prev-page')
    this.nextPageBtn = this.getByTestId('inventory-next-page')
    
    // Table rows
    this.tableRow = this.getByTestId('inventory-row')
    
    // Fallbacks
    this.pageTitleFallback = page.getByRole('heading', { name: 'Inventory' })
  }

  async goto() {
    await this.page.goto('/inventory')
  }

  async isOnPage() {
    return this.page.url().includes('/inventory')
  }

  /**
   * Get row count
   */
  async getRowCount() {
    return this.tableRow.count()
  }

  /**
   * Search inventory
   */
  async search(query) {
    const searchInput = this.searchInput.or(this.page.getByPlaceholder('Search'))
    await searchInput.fill(query)
    await this.page.waitForTimeout(300)
  }

  /**
   * Filter by location
   */
  async filterByLocation(locationName) {
    await this.locationFilter.click()
    await this.page.getByRole('option', { name: locationName }).click()
  }

  /**
   * Toggle expiring soon filter
   */
  async toggleExpiringFilter() {
    await this.expiringFilter.click()
  }

  /**
   * Go to next page
   */
  async nextPage() {
    await this.nextPageBtn.click()
  }

  /**
   * Go to previous page
   */
  async prevPage() {
    await this.prevPageBtn.click()
  }

  /**
   * Sort by column
   */
  async sortBy(columnName) {
    await this.page.getByRole('columnheader', { name: columnName }).click()
  }

  /**
   * Get cell value from row
   */
  async getCellValue(rowIndex, columnTestId) {
    return this.tableRow.nth(rowIndex).locator(`[data-testid="${columnTestId}"]`).textContent()
  }

  /**
   * Check if loading
   */
  async isLoading() {
    return this.loadingState.isVisible()
  }

  /**
   * Check if empty
   */
  async isEmpty() {
    return this.emptyState.isVisible()
  }
}
