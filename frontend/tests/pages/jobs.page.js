/**
 * Jobs Page Object
 */
import { BasePage } from './base.page.js'

export class JobsPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Page elements
    this.pageContainer = this.getByTestId('jobs-page')
    this.title = this.getByTestId('jobs-title')
    this.statsCard = this.getByTestId('jobs-stats')
    this.jobsList = this.getByTestId('jobs-list')
    this.loadingState = this.getByTestId('jobs-loading')
    this.emptyState = this.getByTestId('jobs-empty')
    
    // Stats
    this.pendingCount = this.getByTestId('jobs-pending-count')
    this.runningCount = this.getByTestId('jobs-running-count')
    this.completedCount = this.getByTestId('jobs-completed-count')
    this.failedCount = this.getByTestId('jobs-failed-count')
    
    // Filters
    this.statusFilter = this.getByTestId('jobs-status-filter')
    this.typeFilter = this.getByTestId('jobs-type-filter')
    this.refreshBtn = this.getByTestId('jobs-refresh-btn')
    
    // Job item
    this.jobItem = this.getByTestId('job-item')
    
    // Fallbacks
    this.pageTitleFallback = page.getByRole('heading', { name: 'Jobs' })
  }

  async goto() {
    await this.page.goto('/jobs')
  }

  async isOnPage() {
    return this.page.url().includes('/jobs')
  }

  /**
   * Get job count
   */
  async getJobCount() {
    return this.jobItem.count()
  }

  /**
   * Filter by status
   */
  async filterByStatus(status) {
    await this.statusFilter.click()
    await this.page.getByRole('option', { name: status }).click()
  }

  /**
   * Refresh job list
   */
  async refresh() {
    await this.refreshBtn.click()
  }

  /**
   * Get pending count value
   */
  async getPendingCount() {
    const text = await this.pendingCount.textContent()
    return parseInt(text, 10)
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
