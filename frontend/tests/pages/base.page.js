/**
 * Base Page Object class
 * 
 * All page objects should extend this class to inherit common functionality.
 */
export class BasePage {
  /**
   * @param {import('@playwright/test').Page} page - Playwright page instance
   */
  constructor(page) {
    this.page = page
  }

  /**
   * Navigate to this page's URL
   * Must be implemented by subclasses
   */
  async goto() {
    throw new Error('goto() must be implemented by subclass')
  }

  /**
   * Wait for page to be fully loaded
   * Override in subclasses for page-specific loading indicators
   */
  async waitForLoad() {
    await this.page.waitForLoadState('networkidle')
  }

  /**
   * Navigate to page and wait for it to load
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
   * Must be implemented by subclasses
   */
  async isOnPage() {
    throw new Error('isOnPage() must be implemented by subclass')
  }

  /**
   * Wait for a notification/toast message
   * @param {string} text - Text to look for in notification
   * @param {string} type - Notification type (success, error, warning, info)
   */
  async waitForNotification(text, type = null) {
    const notification = this.page.locator('.q-notification')
    await notification.waitFor({ state: 'visible' })
    if (text) {
      await this.page.getByText(text).waitFor({ state: 'visible' })
    }
  }

  /**
   * Dismiss any visible notifications
   */
  async dismissNotifications() {
    const notifications = this.page.locator('.q-notification')
    const count = await notifications.count()
    for (let i = 0; i < count; i++) {
      const closeBtn = notifications.nth(i).locator('button')
      if (await closeBtn.isVisible()) {
        await closeBtn.click()
      }
    }
  }

  /**
   * Wait for API call to complete
   * @param {string} urlPattern - URL pattern to match
   */
  async waitForApi(urlPattern) {
    await this.page.waitForResponse(
      response => response.url().includes(urlPattern) && response.status() === 200
    )
  }

  /**
   * Take a screenshot with a descriptive name
   * @param {string} name - Screenshot name
   */
  async screenshot(name) {
    await this.page.screenshot({ 
      path: `test-results/screenshots/${name}.png`,
      fullPage: true 
    })
  }
}
