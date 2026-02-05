/**
 * Scan Page Object
 */
import { BasePage } from './base.page.js'

export class ScanPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Page container
    this.pageContainer = this.getByTestId('scan-page')
    
    // Device registration
    this.devicePrompt = this.getByTestId('scan-device-prompt')
    this.deviceRegisterBtn = this.getByTestId('scan-device-register-btn')
    
    // Action mode
    this.actionModeToggle = this.getByTestId('scan-action-mode')
    
    // Location selector
    this.locationSelector = this.getByTestId('scan-location-selector')
    
    // Barcode input
    this.barcodeInput = this.getByTestId('scan-barcode-input')
    this.cameraButton = this.getByTestId('scan-camera-button')
    this.lookupButton = this.getByTestId('scan-lookup-btn')
    
    // Result display
    this.resultCard = this.getByTestId('scan-result-card')
    this.quickAddBtn = this.getByTestId('scan-quick-add')
    this.quickConsumeBtn = this.getByTestId('scan-quick-consume')
    
    // Recent scans
    this.recentScansCard = this.getByTestId('scan-recent-card')
    this.recentScansList = this.getByTestId('scan-recent-list')
    this.recentScanItem = this.getByTestId('scan-recent-item')
    
    // Device dialog
    this.deviceDialog = this.getByTestId('device-dialog')
    this.deviceDialogCard = this.getByTestId('device-dialog-card')
    this.deviceNameInput = this.getByTestId('device-name-input')
    this.deviceRegisterSubmit = this.getByTestId('device-register-submit')
    
    // Product review dialog
    this.reviewDialog = this.getByTestId('product-review-dialog')
    this.reviewNameInput = this.getByTestId('product-review-name-input')
    this.reviewQuantityInput = this.getByTestId('product-review-quantity')
    this.reviewLocationSelect = this.getByTestId('product-review-location')
    this.reviewCancelBtn = this.getByTestId('product-review-cancel')
    this.reviewConfirmBtn = this.getByTestId('product-review-confirm')
    this.reviewCreateBtn = this.getByTestId('product-review-create')
    
    // Fallback selectors
    this.pageTitleFallback = page.getByRole('heading', { name: 'Scan' })
    this.barcodeInputFallback = page.getByPlaceholder('Scan or enter barcode')
  }

  async goto() {
    await this.page.goto('/scan')
  }

  async isOnPage() {
    return this.page.url().includes('/scan')
  }

  /**
   * Get barcode input (with fallback)
   */
  getBarcodeInput() {
    return this.barcodeInput.or(this.barcodeInputFallback)
  }

  /**
   * Enter a barcode
   */
  async enterBarcode(barcode) {
    await this.getBarcodeInput().fill(barcode)
  }

  /**
   * Submit barcode lookup
   */
  async lookup() {
    await this.lookupButton.click()
  }

  /**
   * Enter barcode and lookup
   */
  async scanBarcode(barcode) {
    await this.enterBarcode(barcode)
    await this.lookup()
  }

  /**
   * Toggle camera
   */
  async toggleCamera() {
    await this.cameraButton.click()
  }

  /**
   * Set action mode
   * @param {'add'|'consume'|'transfer'} mode
   */
  async setActionMode(mode) {
    const modeMap = { add: 'Add Stock', consume: 'Consume', transfer: 'Transfer' }
    await this.page.getByRole('button', { name: modeMap[mode] }).click()
  }

  /**
   * Check if device registration prompt is shown
   */
  async hasDevicePrompt() {
    return this.devicePrompt.isVisible().catch(() => 
      this.page.getByText('Register this device').isVisible()
    )
  }

  /**
   * Open device registration dialog
   */
  async openDeviceDialog() {
    await this.deviceRegisterBtn.click()
  }

  /**
   * Register device
   */
  async registerDevice(name) {
    await this.openDeviceDialog()
    await this.deviceNameInput.fill(name)
    await this.deviceRegisterSubmit.click()
  }

  /**
   * Check if review dialog is open
   */
  async isReviewDialogOpen() {
    return this.reviewDialog.isVisible().catch(() => false)
  }

  /**
   * Confirm product in review dialog
   */
  async confirmReview() {
    await this.reviewConfirmBtn.click()
  }

  /**
   * Cancel review dialog
   */
  async cancelReview() {
    await this.reviewCancelBtn.click()
  }

  /**
   * Create product from review dialog
   */
  async createProduct() {
    await this.reviewCreateBtn.click()
  }

  /**
   * Get recent scans count
   */
  async getRecentScansCount() {
    const items = this.page.locator('[data-testid="scan-recent-item"]')
    return items.count()
  }
}
