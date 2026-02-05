/**
 * Locations Page Object
 */
import { BasePage } from './base.page.js'

export class LocationsPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Page elements
    this.pageContainer = this.getByTestId('locations-page')
    this.addButton = this.getByTestId('location-add-btn')
    this.loadingState = this.getByTestId('locations-loading')
    this.emptyState = this.getByTestId('locations-empty')
    this.locationTree = this.getByTestId('location-tree')
    
    // Location row elements
    this.locationRow = page.locator('[data-testid^="location-row-"]')
    this.moveUpBtn = this.getByTestId('location-move-up-btn')
    this.moveDownBtn = this.getByTestId('location-move-down-btn')
    this.addChildBtn = this.getByTestId('location-add-child-btn')
    this.editBtn = this.getByTestId('location-edit-btn')
    this.deleteBtn = this.getByTestId('location-delete-btn')
    
    // Edit/Add dialog
    this.editDialog = this.getByTestId('location-edit-dialog')
    this.nameInput = this.getByTestId('location-name-input')
    this.parentSelect = this.getByTestId('location-parent-select')
    this.freezerToggle = this.getByTestId('location-freezer-toggle')
    this.saveBtn = this.getByTestId('location-save-btn')
    
    // Delete confirmation
    this.deleteConfirmBtn = this.getByTestId('location-delete-confirm')
    
    // Fallbacks
    this.pageTitleFallback = page.getByText('Locations')
    this.addButtonFallback = page.getByRole('button', { name: /add location/i })
  }

  async goto() {
    await this.page.goto('/locations')
  }

  async isOnPage() {
    return this.page.url().includes('/locations')
  }

  /**
   * Get location count
   */
  async getLocationCount() {
    return this.locationRow.count()
  }

  /**
   * Open add location dialog
   */
  async openAddDialog() {
    await this.addButton.or(this.addButtonFallback).click()
  }

  /**
   * Fill location form
   */
  async fillLocationForm({ name, description, type, isFreezer }) {
    if (name) await this.nameInput.fill(name)
    if (description) {
      await this.page.locator('input[aria-label="Description"], input[label="Description"]').fill(description)
    }
    if (type) {
      await this.page.locator('label:has-text("Type") + div').click()
      await this.page.getByRole('option', { name: type }).click()
    }
    if (isFreezer !== undefined && isFreezer) {
      await this.freezerToggle.click()
    }
  }

  /**
   * Save location
   */
  async saveLocation() {
    await this.saveBtn.click()
  }

  /**
   * Add new location
   */
  async addLocation({ name, description, type, isFreezer }) {
    await this.openAddDialog()
    await this.fillLocationForm({ name, description, type, isFreezer })
    await this.saveLocation()
  }

  /**
   * Edit location by name
   */
  async editLocation(name) {
    await this.page.locator(`[data-testid^="location-row-"]:has-text("${name}") [data-testid="location-edit-btn"]`).click()
  }

  /**
   * Delete location by name
   */
  async deleteLocation(name) {
    await this.page.locator(`[data-testid^="location-row-"]:has-text("${name}") [data-testid="location-delete-btn"]`).click()
  }

  /**
   * Confirm delete
   */
  async confirmDelete() {
    await this.deleteConfirmBtn.click()
  }

  /**
   * Check if dialog is open
   */
  async isDialogOpen() {
    return this.editDialog.isVisible()
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
    return this.emptyState.isVisible().catch(() => 
      this.page.getByText('No locations configured').isVisible()
    )
  }
}
