/**
 * Logs Page Object
 * 
 * Encapsulates all interactions with the application logs page.
 */
import { BasePage } from './base.page.js'

export class LogsPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Filters
    this.levelFilter = page.getByTestId('logs-level-filter')
    this.searchInput = page.getByTestId('logs-search-input')
    this.sortOrderButton = page.getByTestId('logs-sort-order')
    this.followModeToggle = page.getByTestId('logs-follow-mode')
    
    // Actions
    this.refreshButton = page.getByTestId('logs-refresh-button')
    this.copyAllButton = page.getByTestId('logs-copy-all-button')
    this.downloadButton = page.getByTestId('logs-download-button')
    this.clearButton = page.getByTestId('logs-clear-button')
    
    // Log display
    this.logContainer = page.getByTestId('logs-container')
    this.logEntries = page.getByTestId('log-entry')
    this.emptyState = page.getByText(/no logs/i)
    
    // Page elements
    this.pageTitle = page.getByRole('heading', { name: /logs|application logs/i })
    this.loadingIndicator = page.locator('.q-spinner')
  }

  async goto() {
    await this.page.goto('/logs')
  }

  async isOnPage() {
    return this.page.url().includes('/logs')
  }

  async waitForLoad() {
    await this.pageTitle.waitFor({ state: 'visible' })
  }

  /**
   * Filter by log level
   * @param {'all' | 'debug' | 'info' | 'warning' | 'error'} level 
   */
  async filterByLevel(level) {
    const filter = await this.levelFilter.isVisible().catch(() => false)
      ? this.levelFilter
      : this.page.getByLabel(/level/i)
    await filter.click()
    await this.page.getByRole('option', { name: new RegExp(level, 'i') }).click()
  }

  /**
   * Search logs
   * @param {string} query 
   */
  async search(query) {
    const input = await this.searchInput.isVisible().catch(() => false)
      ? this.searchInput
      : this.page.getByPlaceholder(/search/i)
    await input.fill(query)
  }

  /**
   * Clear search
   */
  async clearSearch() {
    const input = await this.searchInput.isVisible().catch(() => false)
      ? this.searchInput
      : this.page.getByPlaceholder(/search/i)
    await input.clear()
  }

  /**
   * Toggle sort order (newest/oldest first)
   */
  async toggleSortOrder() {
    const btn = await this.sortOrderButton.isVisible().catch(() => false)
      ? this.sortOrderButton
      : this.page.getByRole('button', { name: /sort|order/i })
    await btn.click()
  }

  /**
   * Toggle follow mode (auto-scroll)
   */
  async toggleFollowMode() {
    const toggle = await this.followModeToggle.isVisible().catch(() => false)
      ? this.followModeToggle
      : this.page.getByLabel(/follow/i)
    await toggle.click()
  }

  /**
   * Refresh logs
   */
  async refresh() {
    const btn = await this.refreshButton.isVisible().catch(() => false)
      ? this.refreshButton
      : this.page.getByRole('button', { name: /refresh/i })
    await btn.click()
  }

  /**
   * Copy all logs to clipboard
   */
  async copyAll() {
    const btn = await this.copyAllButton.isVisible().catch(() => false)
      ? this.copyAllButton
      : this.page.getByRole('button', { name: /copy/i })
    await btn.click()
  }

  /**
   * Download logs
   */
  async download() {
    const btn = await this.downloadButton.isVisible().catch(() => false)
      ? this.downloadButton
      : this.page.getByRole('button', { name: /download/i })
    await btn.click()
  }

  /**
   * Clear logs
   */
  async clearLogs() {
    const btn = await this.clearButton.isVisible().catch(() => false)
      ? this.clearButton
      : this.page.getByRole('button', { name: /clear/i })
    await btn.click()
    // Confirm if needed
    const confirmBtn = this.page.getByRole('button', { name: /confirm|yes/i })
    if (await confirmBtn.isVisible()) {
      await confirmBtn.click()
    }
  }

  /**
   * Get count of visible log entries
   */
  async getLogCount() {
    const entries = this.page.locator('[data-testid="log-entry"], .log-entry, .log-line')
    return await entries.count()
  }

  /**
   * Get log entry data
   * @param {number} index - 0-based index
   */
  async getLogEntry(index) {
    const entries = this.page.locator('[data-testid="log-entry"], .log-entry, .log-line')
    const entry = entries.nth(index)
    return {
      text: await entry.textContent(),
      level: await this.getLogEntryLevel(entry)
    }
  }

  /**
   * Get log level from entry element
   * @param {import('@playwright/test').Locator} entry 
   */
  async getLogEntryLevel(entry) {
    const classes = await entry.getAttribute('class') || ''
    const text = await entry.textContent() || ''
    
    if (classes.includes('error') || text.includes('ERROR')) return 'error'
    if (classes.includes('warning') || text.includes('WARNING')) return 'warning'
    if (classes.includes('info') || text.includes('INFO')) return 'info'
    if (classes.includes('debug') || text.includes('DEBUG')) return 'debug'
    return 'unknown'
  }

  /**
   * Check if logs contain text
   * @param {string} text 
   */
  async containsText(text) {
    const container = await this.logContainer.isVisible().catch(() => false)
      ? this.logContainer
      : this.page.locator('.logs-container, .log-viewer')
    const content = await container.textContent()
    return content.includes(text)
  }

  /**
   * Check if empty state is shown
   */
  async isEmpty() {
    return await this.emptyState.isVisible()
  }
}
