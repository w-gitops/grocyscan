/**
 * Scan Page Object
 * 
 * Encapsulates all interactions with the barcode scanning page.
 */
import { BasePage } from './base.page.js'

export class ScanPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Scanner elements
    this.barcodeInput = page.getByTestId('scan-barcode-input')
    this.submitButton = page.getByTestId('scan-submit')
    this.cameraButton = page.getByTestId('scan-camera-button')
    this.scannerGunModeToggle = page.getByTestId('scan-gun-mode')
    
    // Feedback area
    this.feedbackArea = page.getByTestId('scan-feedback')
    this.feedbackMessage = page.getByTestId('scan-feedback-message')
    
    // Location selector
    this.locationSelector = page.getByTestId('scan-location-selector')
    this.locationDropdown = page.getByTestId('scan-location-dropdown')
    
    // Action mode
    this.actionModeSelector = page.getByTestId('scan-action-mode')
    
    // Recent scans
    this.recentScans = page.getByTestId('scan-recent-list')
    this.recentScansEmpty = page.getByText('No recent scans')
    
    // Camera dialog
    this.cameraDialog = page.getByRole('dialog')
    this.cameraDialogClose = page.getByRole('button', { name: /cancel|close/i })
    
    // Product review dialog
    this.reviewDialog = page.getByTestId('product-review-dialog')
    this.reviewDialogTitle = page.getByText('Review Product')
    
    // Fallback selectors
    this.barcodeInputFallback = page.getByPlaceholder(/scan|barcode/i)
    this.pageTitle = page.getByRole('heading', { name: 'Scan' })
  }

  async goto() {
    await this.page.goto('/scan')
  }

  async isOnPage() {
    return this.page.url().includes('/scan')
  }

  async waitForLoad() {
    await this.pageTitle.waitFor({ state: 'visible' })
  }

  /**
   * Get the barcode input element (with fallback)
   */
  async getBarcodeInput() {
    const testId = await this.barcodeInput.isVisible().catch(() => false)
    return testId ? this.barcodeInput : this.barcodeInputFallback
  }

  /**
   * Enter a barcode into the input field
   * @param {string} barcode 
   */
  async enterBarcode(barcode) {
    const input = await this.getBarcodeInput()
    await input.fill(barcode)
  }

  /**
   * Submit the barcode (click submit button)
   */
  async submitBarcode() {
    const submitBtn = await this.submitButton.isVisible().catch(() => false)
      ? this.submitButton
      : this.page.getByRole('button', { name: /search|submit|look/i })
    await submitBtn.click()
  }

  /**
   * Scan a barcode (enter + submit)
   * @param {string} barcode 
   */
  async scanBarcode(barcode) {
    await this.enterBarcode(barcode)
    await this.submitBarcode()
  }

  /**
   * Scan barcode using Enter key
   * @param {string} barcode 
   */
  async scanBarcodeWithEnter(barcode) {
    const input = await this.getBarcodeInput()
    await input.fill(barcode)
    await input.press('Enter')
  }

  /**
   * Open camera scanner dialog
   */
  async openCameraScanner() {
    const cameraBtn = await this.cameraButton.isVisible().catch(() => false)
      ? this.cameraButton
      : this.page.locator('[aria-label*="camera"], button:has(svg[data-icon="qrcode"])')
    await cameraBtn.click()
  }

  /**
   * Close camera dialog
   */
  async closeCameraDialog() {
    await this.cameraDialogClose.click()
  }

  /**
   * Check if camera dialog is open
   */
  async isCameraDialogOpen() {
    return await this.cameraDialog.isVisible()
  }

  /**
   * Select a location from the dropdown
   * @param {string} locationName 
   */
  async selectLocation(locationName) {
    await this.locationSelector.click()
    await this.page.getByRole('option', { name: locationName }).click()
  }

  /**
   * Set action mode (Add Stock, Consume, Transfer)
   * @param {'add' | 'consume' | 'transfer'} mode 
   */
  async setActionMode(mode) {
    const modeSelector = await this.actionModeSelector.isVisible().catch(() => false)
      ? this.actionModeSelector
      : this.page.locator('.q-btn-toggle, .q-tabs')
    
    const modeLabels = {
      add: /add|stock/i,
      consume: /consume/i,
      transfer: /transfer/i
    }
    
    await modeSelector.getByText(modeLabels[mode]).click()
  }

  /**
   * Toggle scanner gun mode
   */
  async toggleScannerGunMode() {
    const toggle = await this.scannerGunModeToggle.isVisible().catch(() => false)
      ? this.scannerGunModeToggle
      : this.page.locator('[aria-label*="gun mode"], [title*="gun mode"]')
    await toggle.click()
  }

  /**
   * Wait for scan feedback to appear
   * @param {'success' | 'error' | 'warning' | 'info'} type 
   */
  async waitForFeedback(type = null) {
    await this.feedbackArea.waitFor({ state: 'visible' })
    if (type) {
      const colorClass = {
        success: 'green',
        error: 'red',
        warning: 'orange',
        info: 'blue'
      }[type]
      await this.page.locator(`[class*="${colorClass}"]`).waitFor({ state: 'visible' })
    }
  }

  /**
   * Get feedback message text
   */
  async getFeedbackMessage() {
    const msg = await this.feedbackMessage.isVisible().catch(() => false)
      ? this.feedbackMessage
      : this.feedbackArea
    return await msg.textContent()
  }

  /**
   * Check if product review dialog is open
   */
  async isReviewDialogOpen() {
    const dialog = await this.reviewDialog.isVisible().catch(() => false)
    if (dialog) return true
    return await this.reviewDialogTitle.isVisible().catch(() => false)
  }

  /**
   * Wait for product review dialog
   */
  async waitForReviewDialog() {
    await this.page.waitForSelector('[role="dialog"]', { state: 'visible' })
  }

  /**
   * Get count of recent scans
   */
  async getRecentScansCount() {
    const list = await this.recentScans.isVisible().catch(() => false)
    if (!list) return 0
    return await this.recentScans.locator('> *').count()
  }

  /**
   * Check if recent scans list is empty
   */
  async hasNoRecentScans() {
    return await this.recentScansEmpty.isVisible()
  }
}
