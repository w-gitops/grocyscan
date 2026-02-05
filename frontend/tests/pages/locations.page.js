/**
 * Locations Page Object
 * 
 * Encapsulates all interactions with the locations management page.
 */
import { BasePage } from './base.page.js'

export class LocationsPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Main elements
    this.addButton = page.getByTestId('locations-add-button')
    this.syncButton = page.getByTestId('locations-sync-button')
    this.syncStatus = page.getByTestId('locations-sync-status')
    this.locationList = page.getByTestId('locations-list')
    this.locationCards = page.getByTestId('location-card')
    
    // Add/Edit dialog
    this.dialog = page.getByTestId('location-dialog')
    this.nameInput = page.getByTestId('location-name-input')
    this.descriptionInput = page.getByTestId('location-description-input')
    this.typeSelect = page.getByTestId('location-type-select')
    this.freezerToggle = page.getByTestId('location-freezer-toggle')
    this.saveButton = page.getByTestId('location-save-button')
    this.cancelButton = page.getByTestId('location-cancel-button')
    this.deleteButton = page.getByTestId('location-delete-button')
    
    // Detail dialog
    this.detailDialog = page.getByTestId('location-detail-dialog')
    this.editButton = page.getByTestId('location-edit-button')
    
    // Fallback selectors
    this.addButtonFallback = page.getByRole('button', { name: /add location/i })
    this.syncButtonFallback = page.getByRole('button', { name: /sync/i })
    this.pageTitle = page.getByRole('heading', { name: 'Locations' })
    this.emptyState = page.getByText(/no locations/i)
  }

  async goto() {
    await this.page.goto('/locations')
  }

  async isOnPage() {
    return this.page.url().includes('/locations')
  }

  async waitForLoad() {
    await this.pageTitle.waitFor({ state: 'visible' })
  }

  /**
   * Get count of location cards
   */
  async getLocationCount() {
    const cards = this.page.locator('[data-testid="location-card"], .location-card, .q-card')
    return await cards.count()
  }

  /**
   * Click on a location card by name
   * @param {string} locationName 
   */
  async clickLocation(locationName) {
    await this.page.getByText(locationName).first().click()
  }

  /**
   * Open add location dialog
   */
  async openAddDialog() {
    const btn = await this.addButton.isVisible().catch(() => false)
      ? this.addButton
      : this.addButtonFallback
    await btn.click()
  }

  /**
   * Fill location form
   * @param {Object} location 
   * @param {string} location.name
   * @param {string} [location.description]
   * @param {string} [location.type]
   * @param {boolean} [location.isFreezer]
   */
  async fillLocationForm({ name, description, type, isFreezer }) {
    if (name) {
      const nameField = await this.nameInput.isVisible().catch(() => false)
        ? this.nameInput
        : this.page.getByLabel(/name/i).first()
      await nameField.fill(name)
    }
    if (description) {
      const descField = await this.descriptionInput.isVisible().catch(() => false)
        ? this.descriptionInput
        : this.page.getByLabel(/description/i)
      await descField.fill(description)
    }
    if (type) {
      const typeField = await this.typeSelect.isVisible().catch(() => false)
        ? this.typeSelect
        : this.page.getByLabel(/type/i)
      await typeField.click()
      await this.page.getByRole('option', { name: type }).click()
    }
    if (isFreezer !== undefined) {
      const toggle = await this.freezerToggle.isVisible().catch(() => false)
        ? this.freezerToggle
        : this.page.getByLabel(/freezer/i)
      const isChecked = await toggle.isChecked()
      if (isChecked !== isFreezer) {
        await toggle.click()
      }
    }
  }

  /**
   * Save location form
   */
  async saveLocation() {
    const btn = await this.saveButton.isVisible().catch(() => false)
      ? this.saveButton
      : this.page.getByRole('button', { name: /save|create/i })
    await btn.click()
  }

  /**
   * Cancel location form
   */
  async cancelForm() {
    const btn = await this.cancelButton.isVisible().catch(() => false)
      ? this.cancelButton
      : this.page.getByRole('button', { name: /cancel/i })
    await btn.click()
  }

  /**
   * Create a new location
   * @param {Object} location 
   */
  async createLocation(location) {
    await this.openAddDialog()
    await this.fillLocationForm(location)
    await this.saveLocation()
  }

  /**
   * Trigger Grocy sync
   */
  async syncWithGrocy() {
    const btn = await this.syncButton.isVisible().catch(() => false)
      ? this.syncButton
      : this.syncButtonFallback
    await btn.click()
  }

  /**
   * Get sync status text
   */
  async getSyncStatus() {
    const status = await this.syncStatus.isVisible().catch(() => false)
      ? this.syncStatus
      : this.page.locator('.sync-status, [class*="sync"]')
    return await status.textContent()
  }

  /**
   * Check if dialog is open
   */
  async isDialogOpen() {
    return await this.dialog.isVisible().catch(() => false) ||
           await this.detailDialog.isVisible().catch(() => false) ||
           await this.page.getByRole('dialog').isVisible()
  }

  /**
   * Close any open dialog
   */
  async closeDialog() {
    await this.page.getByRole('button', { name: /close|×/i }).click()
  }

  /**
   * Delete location from detail view
   */
  async deleteLocation() {
    const btn = await this.deleteButton.isVisible().catch(() => false)
      ? this.deleteButton
      : this.page.getByRole('button', { name: /delete/i })
    await btn.click()
    // Confirm if needed
    const confirmBtn = this.page.getByRole('button', { name: /confirm|yes/i })
    if (await confirmBtn.isVisible()) {
      await confirmBtn.click()
    }
  }

  /**
   * Open edit mode from detail view
   */
  async openEditMode() {
    const btn = await this.editButton.isVisible().catch(() => false)
      ? this.editButton
      : this.page.getByRole('button', { name: /edit/i })
    await btn.click()
  }

  /**
   * Check if location has freezer indicator
   * @param {string} locationName 
   */
  async hasFreezerIndicator(locationName) {
    const card = this.page.locator('.q-card').filter({ hasText: locationName })
    return await card.locator('[class*="freezer"], .snowflake, svg[data-icon="snowflake"]').isVisible()
  }
}
