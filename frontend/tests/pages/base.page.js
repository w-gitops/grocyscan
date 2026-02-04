/**
 * Base Page Object class
 * All page objects should extend this class
 */
export class BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    this.page = page
  }

  /**
   * Navigate to this page's URL
   * Must be implemented by subclass
   */
  async goto() {
    throw new Error('goto() must be implemented by subclass')
  }

  /**
   * Wait for page to be fully loaded
   */
  async waitForLoad() {
    await this.page.waitForLoadState('networkidle')
  }

  /**
   * Navigate to page and wait for load
   */
  async navigate() {
    await this.goto()
    await this.waitForLoad()
  }

  /**
   * Get current URL path
   */
  async getPath() {
    const url = new URL(this.page.url())
    return url.pathname
  }

  /**
   * Check if currently on this page
   * Must be implemented by subclass
   */
  async isOnPage() {
    throw new Error('isOnPage() must be implemented by subclass')
  }

  /**
   * Wait for a notification to appear
   * @param {string} text - Text to look for in notification
   * @param {string|null} type - Optional notification type (positive, negative, warning, info)
   */
  async waitForNotification(text, type = null) {
    const selector = type 
      ? `.q-notification.bg-${type}:has-text("${text}")`
      : `.q-notification:has-text("${text}")`
    await this.page.waitForSelector(selector, { timeout: 5000 })
  }

  /**
   * Dismiss all visible notifications
   */
  async dismissNotifications() {
    const closeButtons = this.page.locator('.q-notification button[aria-label="Close"]')
    const count = await closeButtons.count()
    for (let i = 0; i < count; i++) {
      await closeButtons.nth(i).click().catch(() => {})
    }
  }

  /**
   * Wait for an API response
   * @param {string|RegExp} urlPattern - URL pattern to match
   */
  async waitForApi(urlPattern) {
    return this.page.waitForResponse(urlPattern)
  }

  /**
   * Take a screenshot with a descriptive name
   * @param {string} name - Screenshot name (without extension)
   */
  async screenshot(name) {
    await this.page.screenshot({ 
      path: `test-results/screenshots/${name}.png`,
      fullPage: true 
    })
  }

  /**
   * Get element by data-testid
   * @param {string} testId - The data-testid value
   */
  getByTestId(testId) {
    return this.page.locator(`[data-testid="${testId}"]`)
  }

  /**
   * Check if element with data-testid exists and is visible
   * @param {string} testId - The data-testid value
   */
  async isTestIdVisible(testId) {
    return this.getByTestId(testId).isVisible()
  }
}
