/**
 * Inventory Page Object
 * 
 * Encapsulates all interactions with the stock/inventory page.
 */
import { BasePage } from './base.page.js'

export class InventoryPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Table and data
    this.stockTable = page.getByTestId('inventory-table')
    this.tableRows = page.locator('tbody tr')
    this.emptyState = page.getByText(/no stock|no inventory|empty/i)
    
    // Column headers for sorting
    this.productHeader = page.getByRole('columnheader', { name: /product/i })
    this.locationHeader = page.getByRole('columnheader', { name: /location/i })
    this.quantityHeader = page.getByRole('columnheader', { name: /quantity/i })
    this.expirationHeader = page.getByRole('columnheader', { name: /expir|best before/i })
    
    // Pagination
    this.pagination = page.getByTestId('inventory-pagination')
    this.nextPageButton = page.getByRole('button', { name: /next/i })
    this.prevPageButton = page.getByRole('button', { name: /prev/i })
    this.rowsPerPage = page.getByTestId('inventory-rows-per-page')
    
    // Filters
    this.searchInput = page.getByTestId('inventory-search')
    this.locationFilter = page.getByTestId('inventory-location-filter')
    this.expiredOnlyToggle = page.getByTestId('inventory-expired-only')
    
    // Page elements
    this.pageTitle = page.getByRole('heading', { name: /inventory|stock/i })
    this.loadingIndicator = page.locator('.q-spinner')
  }

  async goto() {
    await this.page.goto('/inventory')
  }

  async isOnPage() {
    return this.page.url().includes('/inventory')
  }

  async waitForLoad() {
    await this.pageTitle.waitFor({ state: 'visible' })
    // Wait for table or empty state
    await Promise.race([
      this.stockTable.waitFor({ state: 'visible' }).catch(() => {}),
      this.emptyState.waitFor({ state: 'visible' }).catch(() => {}),
      this.page.waitForTimeout(3000)
    ])
  }

  /**
   * Get count of rows in the table
   */
  async getRowCount() {
    return await this.tableRows.count()
  }

  /**
   * Sort table by column
   * @param {'product' | 'location' | 'quantity' | 'expiration'} column 
   */
  async sortBy(column) {
    const headers = {
      product: this.productHeader,
      location: this.locationHeader,
      quantity: this.quantityHeader,
      expiration: this.expirationHeader
    }
    await headers[column].click()
  }

  /**
   * Search inventory
   * @param {string} query 
   */
  async search(query) {
    const input = await this.searchInput.isVisible().catch(() => false)
      ? this.searchInput
      : this.page.getByPlaceholder(/search/i)
    await input.fill(query)
  }

  /**
   * Filter by location
   * @param {string} location 
   */
  async filterByLocation(location) {
    await this.locationFilter.click()
    await this.page.getByRole('option', { name: location }).click()
  }

  /**
   * Toggle expired items only filter
   */
  async toggleExpiredOnly() {
    await this.expiredOnlyToggle.click()
  }

  /**
   * Go to next page
   */
  async nextPage() {
    await this.nextPageButton.click()
  }

  /**
   * Go to previous page
   */
  async prevPage() {
    await this.prevPageButton.click()
  }

  /**
   * Set rows per page
   * @param {number} count 
   */
  async setRowsPerPage(count) {
    await this.rowsPerPage.click()
    await this.page.getByRole('option', { name: String(count) }).click()
  }

  /**
   * Get data from a specific row
   * @param {number} index - 0-based row index
   */
  async getRowData(index) {
    const row = this.tableRows.nth(index)
    const cells = row.locator('td')
    return {
      product: await cells.nth(0).textContent(),
      location: await cells.nth(1).textContent(),
      quantity: await cells.nth(2).textContent(),
      expiration: await cells.nth(3).textContent()
    }
  }

  /**
   * Click on a row to view details
   * @param {number} index - 0-based row index
   */
  async clickRow(index) {
    await this.tableRows.nth(index).click()
  }

  /**
   * Check if table is empty
   */
  async isEmpty() {
    const rowCount = await this.getRowCount()
    return rowCount === 0 || await this.emptyState.isVisible()
  }
}
