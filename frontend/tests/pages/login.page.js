/**
 * Login Page Object
 */
import { BasePage } from './base.page.js'

export class LoginPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Primary selectors using data-testid
    this.card = this.getByTestId('login-card')
    this.title = this.getByTestId('login-title')
    this.form = this.getByTestId('login-form')
    this.usernameInput = this.getByTestId('login-username')
    this.passwordInput = this.getByTestId('login-password')
    this.passwordToggle = this.getByTestId('login-password-toggle')
    this.submitButton = this.getByTestId('login-submit')
    this.errorBanner = this.getByTestId('login-error')
    
    // Fallback selectors for when data-testid not available
    this.usernameInputFallback = page.getByLabel('Username')
    this.passwordInputFallback = page.getByLabel('Password')
    this.submitButtonFallback = page.getByRole('button', { name: /sign in/i })
  }

  async goto() {
    await this.page.goto('/login')
  }

  async isOnPage() {
    return this.page.url().includes('/login')
  }

  /**
   * Get username input (with fallback)
   */
  getUsernameInput() {
    return this.usernameInput.or(this.usernameInputFallback)
  }

  /**
   * Get password input (with fallback)
   */
  getPasswordInput() {
    return this.passwordInput.or(this.passwordInputFallback)
  }

  /**
   * Get submit button (with fallback)
   */
  getSubmitButton() {
    return this.submitButton.or(this.submitButtonFallback)
  }

  /**
   * Fill login form
   */
  async fillCredentials(username, password) {
    await this.getUsernameInput().fill(username)
    await this.getPasswordInput().fill(password)
  }

  /**
   * Submit the login form
   */
  async submit() {
    await this.getSubmitButton().click()
  }

  /**
   * Complete login flow
   */
  async login(username, password) {
    await this.fillCredentials(username, password)
    await this.submit()
  }

  /**
   * Toggle password visibility
   */
  async togglePasswordVisibility() {
    await this.passwordToggle.click()
  }

  /**
   * Check if error is displayed
   */
  async hasError() {
    return this.errorBanner.isVisible()
  }

  /**
   * Get error message text
   */
  async getErrorText() {
    if (await this.errorBanner.isVisible()) {
      return this.errorBanner.textContent()
    }
    return null
  }

  /**
   * Check if sign in text is visible
   */
  async hasSignInText() {
    return this.page.getByText('Sign in to continue').isVisible()
  }
}
