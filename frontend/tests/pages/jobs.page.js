/**
 * Jobs Page Object
 * 
 * Encapsulates all interactions with the job queue page.
 */
import { BasePage } from './base.page.js'

export class JobsPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Stats cards
    this.pendingStat = page.getByTestId('jobs-stat-pending')
    this.runningStat = page.getByTestId('jobs-stat-running')
    this.completedStat = page.getByTestId('jobs-stat-completed')
    this.failedStat = page.getByTestId('jobs-stat-failed')
    
    // Filters
    this.statusFilter = page.getByTestId('jobs-status-filter')
    this.typeFilter = page.getByTestId('jobs-type-filter')
    this.refreshButton = page.getByTestId('jobs-refresh-button')
    
    // Job list
    this.jobList = page.getByTestId('jobs-list')
    this.jobCards = page.getByTestId('job-card')
    this.emptyState = page.getByText(/no jobs/i)
    
    // Job detail
    this.jobDetail = page.getByTestId('job-detail')
    this.retryButton = page.getByTestId('job-retry-button')
    this.cancelButton = page.getByTestId('job-cancel-button')
    
    // Page elements
    this.pageTitle = page.getByRole('heading', { name: /job queue|jobs/i })
    this.loadingIndicator = page.locator('.q-spinner')
  }

  async goto() {
    await this.page.goto('/jobs')
  }

  async isOnPage() {
    return this.page.url().includes('/jobs')
  }

  async waitForLoad() {
    await this.pageTitle.waitFor({ state: 'visible' })
  }

  /**
   * Get job stats
   */
  async getStats() {
    const getText = async (locator, fallbackText) => {
      try {
        if (await locator.isVisible()) {
          return await locator.textContent()
        }
      } catch {}
      // Fallback: find by label
      const card = this.page.locator('.q-card').filter({ hasText: fallbackText })
      const value = card.locator('.text-h4, .text-h5, .stat-value')
      return await value.textContent()
    }

    return {
      pending: await getText(this.pendingStat, 'Pending'),
      running: await getText(this.runningStat, 'Running'),
      completed: await getText(this.completedStat, 'Completed'),
      failed: await getText(this.failedStat, 'Failed')
    }
  }

  /**
   * Filter by status
   * @param {'all' | 'pending' | 'running' | 'completed' | 'failed'} status 
   */
  async filterByStatus(status) {
    const filter = await this.statusFilter.isVisible().catch(() => false)
      ? this.statusFilter
      : this.page.getByLabel(/status/i)
    await filter.click()
    await this.page.getByRole('option', { name: new RegExp(status, 'i') }).click()
  }

  /**
   * Get count of visible jobs
   */
  async getJobCount() {
    const cards = this.page.locator('[data-testid="job-card"], .job-card, .q-item')
    return await cards.count()
  }

  /**
   * Click on a job to view details
   * @param {number} index - 0-based index
   */
  async clickJob(index) {
    const cards = this.page.locator('[data-testid="job-card"], .job-card, .q-item')
    await cards.nth(index).click()
  }

  /**
   * Refresh job list
   */
  async refresh() {
    const btn = await this.refreshButton.isVisible().catch(() => false)
      ? this.refreshButton
      : this.page.getByRole('button', { name: /refresh/i })
    await btn.click()
  }

  /**
   * Retry a failed job
   */
  async retryJob() {
    const btn = await this.retryButton.isVisible().catch(() => false)
      ? this.retryButton
      : this.page.getByRole('button', { name: /retry/i })
    await btn.click()
  }

  /**
   * Cancel a running job
   */
  async cancelJob() {
    const btn = await this.cancelButton.isVisible().catch(() => false)
      ? this.cancelButton
      : this.page.getByRole('button', { name: /cancel/i })
    await btn.click()
  }

  /**
   * Check if job detail is open
   */
  async isDetailOpen() {
    return await this.jobDetail.isVisible().catch(() => false) ||
           await this.page.getByRole('dialog').isVisible()
  }

  /**
   * Close job detail
   */
  async closeDetail() {
    await this.page.getByRole('button', { name: /close|×/i }).click()
  }

  /**
   * Get job status badge color class
   * @param {number} index 
   */
  async getJobStatusColor(index) {
    const cards = this.page.locator('[data-testid="job-card"], .job-card, .q-item')
    const badge = cards.nth(index).locator('.q-badge, .status-badge')
    const classes = await badge.getAttribute('class')
    if (classes.includes('green') || classes.includes('positive')) return 'success'
    if (classes.includes('red') || classes.includes('negative')) return 'failed'
    if (classes.includes('orange') || classes.includes('warning')) return 'running'
    return 'pending'
  }

  /**
   * Check if empty state is shown
   */
  async isEmpty() {
    return await this.emptyState.isVisible()
  }
}
