/**
 * Navigation Component Page Object
 * Handles header and navigation interactions
 */
import { BasePage } from '../base.page.js'

export class NavigationComponent extends BasePage {
  constructor(page) {
    super(page)
    
    // Header
    this.header = this.getByTestId('app-header')
    this.appLogo = this.getByTestId('app-logo')
    
    // Desktop navigation
    this.navScan = this.getByTestId('nav-scan')
    this.navProducts = this.getByTestId('nav-products')
    this.navInventory = this.getByTestId('nav-inventory')
    this.navLocations = this.getByTestId('nav-locations')
    this.navJobs = this.getByTestId('nav-jobs')
    this.navLogs = this.getByTestId('nav-logs')
    this.navSettings = this.getByTestId('nav-settings')
    this.logoutBtn = this.getByTestId('nav-logout')
    
    // Mobile navigation
    this.mobileMenuBtn = this.getByTestId('mobile-menu-button')
    this.mobileDrawer = this.getByTestId('mobile-drawer')
    this.mobileNavScan = this.getByTestId('mobile-nav-scan')
    this.mobileNavProducts = this.getByTestId('mobile-nav-products')
    this.mobileNavInventory = this.getByTestId('mobile-nav-inventory')
    this.mobileNavLocations = this.getByTestId('mobile-nav-locations')
    this.mobileNavJobs = this.getByTestId('mobile-nav-jobs')
    this.mobileNavLogs = this.getByTestId('mobile-nav-logs')
    this.mobileNavSettings = this.getByTestId('mobile-nav-settings')
    
    // Fallbacks
    this.scanBtnFallback = page.getByRole('button', { name: 'Scan' })
    this.productsBtnFallback = page.getByRole('button', { name: 'Products' })
    this.settingsBtnFallback = page.getByRole('button', { name: 'Settings' })
    this.menuBtnFallback = page.locator('button[aria-label="Menu"], button:has(> .q-icon:text("menu"))')
  }

  // Not a standalone page, so no goto
  async goto() {
    throw new Error('NavigationComponent is not a standalone page')
  }

  async isOnPage() {
    return true // Always present when logged in
  }

  /**
   * Check if header is visible
   */
  async isHeaderVisible() {
    return this.header.isVisible().catch(() => 
      this.page.locator('header').isVisible()
    )
  }

  /**
   * Navigate to a page via desktop nav
   */
  async navigateTo(pageName) {
    const navMap = {
      scan: this.navScan.or(this.scanBtnFallback),
      products: this.navProducts.or(this.productsBtnFallback),
      inventory: this.navInventory.or(this.page.getByRole('button', { name: 'Inventory' })),
      locations: this.navLocations.or(this.page.getByRole('button', { name: 'Locations' })),
      jobs: this.navJobs.or(this.page.getByRole('button', { name: 'Jobs' })),
      logs: this.navLogs.or(this.page.getByRole('button', { name: 'Logs' })),
      settings: this.navSettings.or(this.settingsBtnFallback)
    }
    
    const navBtn = navMap[pageName.toLowerCase()]
    if (navBtn) {
      await navBtn.click()
    }
  }

  /**
   * Open mobile menu
   */
  async openMobileMenu() {
    const menuBtn = this.mobileMenuBtn.or(this.menuBtnFallback)
    await menuBtn.click()
  }

  /**
   * Check if mobile menu is open
   */
  async isMobileMenuOpen() {
    return this.mobileDrawer.isVisible().catch(() => 
      this.page.locator('.q-drawer').isVisible()
    )
  }

  /**
   * Navigate via mobile menu
   */
  async navigateViaMobile(pageName) {
    await this.openMobileMenu()
    
    const mobileNavMap = {
      scan: this.mobileNavScan,
      products: this.mobileNavProducts,
      inventory: this.mobileNavInventory,
      locations: this.mobileNavLocations,
      jobs: this.mobileNavJobs,
      logs: this.mobileNavLogs,
      settings: this.mobileNavSettings
    }
    
    const navItem = mobileNavMap[pageName.toLowerCase()]
    if (navItem) {
      await navItem.click().catch(async () => {
        // Fallback: click by text in drawer
        await this.page.locator(`.q-drawer .q-item:has-text("${pageName}")`).click()
      })
    } else {
      // Fallback
      await this.page.locator(`.q-drawer .q-item:has-text("${pageName}")`).click()
    }
  }

  /**
   * Logout
   */
  async logout() {
    await this.logoutBtn.or(this.page.locator('button:has(.q-icon:text("logout"))')).click()
  }

  /**
   * Get app title text
   */
  async getAppTitle() {
    return this.appLogo.textContent().catch(() => 
      this.page.locator('.q-toolbar-title').textContent()
    )
  }

  /**
   * Check if on mobile viewport
   */
  async isMobileViewport() {
    const viewport = this.page.viewportSize()
    return viewport && viewport.width < 1024
  }
}
