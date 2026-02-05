/**
 * Logs Page Object
 */
import { BasePage } from './base.page.js'

export class LogsPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Page elements
    this.pageContainer = this.getByTestId('logs-page')
    this.title = this.getByTestId('logs-title')
    this.logsList = this.getByTestId('logs-list')
    this.loadingState = this.getByTestId('logs-loading')
    this.emptyState = this.getByTestId('logs-empty')
    
    // Filters
    this.levelFilter = this.getByTestId('logs-level-filter')
    this.searchInput = this.getByTestId('logs-search')
    this.dateFilter = this.getByTestId('logs-date-filter')
    
    // Actions
    this.refreshBtn = this.getByTestId('logs-refresh-btn')
    this.clearBtn = this.getByTestId('logs-clear-btn')
    this.exportBtn = this.getByTestId('logs-export-btn')
    this.copyBtn = this.getByTestId('logs-copy-btn')
    
    // Log entry
    this.logEntry = this.getByTestId('log-entry')
    
    // Fallbacks
    this.pageTitleFallback = page.getByRole('heading', { name: 'Logs' })
  }

  async goto() {
    await this.page.goto('/logs')
  }

  async isOnPage() {
    return this.page.url().includes('/logs')
  }

  /**
   * Get log entry count
   */
  async getLogCount() {
    return this.logEntry.count()
  }

  /**
   * Filter by level
   */
  async filterByLevel(level) {
    await this.levelFilter.click()
    await this.page.getByRole('option', { name: level }).click()
  }

  /**
   * Search logs
   */
  async search(query) {
    const searchInput = this.searchInput.or(this.page.getByPlaceholder('Search logs'))
    await searchInput.fill(query)
    await this.page.waitForTimeout(300)
  }

  /**
   * Refresh logs
   */
  async refresh() {
    await this.refreshBtn.click()
  }

  /**
   * Clear logs
   */
  async clearLogs() {
    await this.clearBtn.click()
  }

  /**
   * Export logs
   */
  async exportLogs() {
    await this.exportBtn.click()
  }

  /**
   * Copy logs to clipboard
   */
  async copyLogs() {
    await this.copyBtn.click()
  }

  /**
   * Check if loading
   */
  async isLoading() {
    return this.loadingState.isVisible().catch(() => false)
  }

  /**
   * Check if empty
   */
  async isEmpty() {
    return this.emptyState.isVisible().catch(() => false)
  }
}
