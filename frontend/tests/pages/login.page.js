/**
 * Login Page Object
 * 
 * Encapsulates all interactions with the login page.
 */
import { BasePage } from './base.page.js'

export class LoginPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Form elements
    this.usernameInput = page.getByTestId('login-username')
    this.passwordInput = page.getByTestId('login-password')
    this.submitButton = page.getByTestId('login-submit')
    this.errorMessage = page.getByTestId('login-error')
    this.passwordToggle = page.getByTestId('login-password-toggle')
    
    // Fallback selectors (for components without data-testid yet)
    this.usernameInputFallback = page.getByLabel('Username')
    this.passwordInputFallback = page.getByLabel('Password')
    this.submitButtonFallback = page.getByRole('button', { name: /sign in/i })
    
    // Page elements
    this.title = page.getByText('Sign in to continue')
    this.logo = page.getByText('GrocyScan')
  }

  async goto() {
    await this.page.goto('/login')
  }

  async isOnPage() {
    return this.page.url().includes('/login')
  }

  async waitForLoad() {
    await this.title.waitFor({ state: 'visible' })
  }

  /**
   * Fill login form with credentials
   * @param {string} username 
   * @param {string} password 
   */
  async fillCredentials(username, password) {
    // Try data-testid first, fall back to label selectors
    const usernameField = await this.usernameInput.isVisible().catch(() => false) 
      ? this.usernameInput 
      : this.usernameInputFallback
    const passwordField = await this.passwordInput.isVisible().catch(() => false)
      ? this.passwordInput
      : this.passwordInputFallback

    await usernameField.fill(username)
    await passwordField.fill(password)
  }

  /**
   * Submit the login form
   */
  async submit() {
    const button = await this.submitButton.isVisible().catch(() => false)
      ? this.submitButton
      : this.submitButtonFallback
    await button.click()
  }

  /**
   * Perform complete login flow
   * @param {string} username 
   * @param {string} password 
   */
  async login(username, password) {
    await this.fillCredentials(username, password)
    await this.submit()
  }

  /**
   * Login and wait for redirect to expected page
   * @param {string} username 
   * @param {string} password 
   * @param {string|RegExp} expectedUrl - URL pattern to wait for after login
   */
  async loginAndWaitForRedirect(username, password, expectedUrl = /\/scan/) {
    await this.login(username, password)
    await this.page.waitForURL(expectedUrl)
  }

  /**
   * Toggle password visibility
   */
  async togglePasswordVisibility() {
    const toggle = await this.passwordToggle.isVisible().catch(() => false)
      ? this.passwordToggle
      : this.page.locator('[aria-label="Toggle password visibility"]')
    await toggle.click()
  }

  /**
   * Check if password is visible (not masked)
   */
  async isPasswordVisible() {
    const passwordField = await this.passwordInput.isVisible().catch(() => false)
      ? this.passwordInput
      : this.passwordInputFallback
    const type = await passwordField.getAttribute('type')
    return type === 'text'
  }

  /**
   * Get error message text
   */
  async getErrorMessage() {
    const error = await this.errorMessage.isVisible().catch(() => false)
      ? this.errorMessage
      : this.page.locator('.q-banner--negative, .text-negative')
    
    if (await error.isVisible()) {
      return await error.textContent()
    }
    return null
  }

  /**
   * Check if error message is displayed
   */
  async hasError() {
    const error = await this.getErrorMessage()
    return error !== null
  }
}
