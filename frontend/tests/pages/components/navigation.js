/**
 * Navigation Component Object
 * 
 * Encapsulates interactions with the header and mobile navigation.
 */
export class NavigationComponent {
  /**
   * @param {import('@playwright/test').Page} page 
   */
  constructor(page) {
    this.page = page
    
    // Header elements
    this.header = page.getByTestId('app-header')
    this.logo = page.getByTestId('app-logo')
    this.logoutButton = page.getByTestId('logout-button')
    
    // Desktop nav buttons
    this.navScan = page.getByTestId('nav-scan')
    this.navProducts = page.getByTestId('nav-products')
    this.navInventory = page.getByTestId('nav-inventory')
    this.navLocations = page.getByTestId('nav-locations')
    this.navJobs = page.getByTestId('nav-jobs')
    this.navLogs = page.getByTestId('nav-logs')
    this.navSettings = page.getByTestId('nav-settings')
    
    // Mobile nav
    this.mobileMenuButton = page.getByTestId('mobile-menu-button')
    this.mobileDrawer = page.getByTestId('mobile-drawer')
    this.mobileNavScan = page.getByTestId('mobile-nav-scan')
    this.mobileNavProducts = page.getByTestId('mobile-nav-products')
    this.mobileNavSettings = page.getByTestId('mobile-nav-settings')
    
    // Fallback selectors
    this.logoFallback = page.getByText('GrocyScan')
    this.logoutButtonFallback = page.getByRole('button', { name: /logout|sign out/i })
  }

  /**
   * Navigate to a page using desktop navigation
   * @param {'scan' | 'products' | 'inventory' | 'locations' | 'jobs' | 'logs' | 'settings'} page 
   */
  async navigateTo(pageName) {
    const navButtons = {
      scan: [this.navScan, /scan/i],
      products: [this.navProducts, /products/i],
      inventory: [this.navInventory, /inventory/i],
      locations: [this.navLocations, /locations/i],
      jobs: [this.navJobs, /jobs/i],
      logs: [this.navLogs, /logs/i],
      settings: [this.navSettings, /settings/i]
    }
    
    const [testIdLocator, textPattern] = navButtons[pageName]
    const btn = await testIdLocator.isVisible().catch(() => false)
      ? testIdLocator
      : this.page.getByRole('button', { name: textPattern })
    
    await btn.click()
  }

  /**
   * Open mobile drawer
   */
  async openMobileMenu() {
    const btn = await this.mobileMenuButton.isVisible().catch(() => false)
      ? this.mobileMenuButton
      : this.page.locator('[aria-label="Menu"], .q-drawer-toggle')
    await btn.click()
  }

  /**
   * Close mobile drawer
   */
  async closeMobileMenu() {
    // Click outside or on close button
    await this.page.keyboard.press('Escape')
  }

  /**
   * Navigate using mobile menu
   * @param {'scan' | 'products' | 'settings'} page 
   */
  async mobileNavigateTo(pageName) {
    await this.openMobileMenu()
    
    const mobileNavButtons = {
      scan: [this.mobileNavScan, /scan/i],
      products: [this.mobileNavProducts, /products/i],
      settings: [this.mobileNavSettings, /settings/i]
    }
    
    const [testIdLocator, textPattern] = mobileNavButtons[pageName]
    const btn = await testIdLocator.isVisible().catch(() => false)
      ? testIdLocator
      : this.mobileDrawer.getByText(textPattern)
    
    await btn.click()
  }

  /**
   * Check if mobile menu is open
   */
  async isMobileMenuOpen() {
    const drawer = await this.mobileDrawer.isVisible().catch(() => false)
    if (drawer) return true
    return await this.page.locator('.q-drawer--open').isVisible()
  }

  /**
   * Logout
   */
  async logout() {
    const btn = await this.logoutButton.isVisible().catch(() => false)
      ? this.logoutButton
      : this.logoutButtonFallback
    await btn.click()
  }

  /**
   * Check if user is logged in (logout button visible)
   */
  async isLoggedIn() {
    return await this.logoutButton.isVisible().catch(() => false) ||
           await this.logoutButtonFallback.isVisible().catch(() => false)
  }

  /**
   * Get header visibility
   */
  async isHeaderVisible() {
    const header = await this.header.isVisible().catch(() => false)
    if (header) return true
    return await this.page.locator('header, .q-header').isVisible()
  }

  /**
   * Check if in mobile view (mobile nav visible)
   */
  async isMobileView() {
    // Check if mobile menu button is visible
    const mobileBtn = await this.mobileMenuButton.isVisible().catch(() => false)
    if (mobileBtn) return true
    return await this.page.locator('.q-drawer-toggle').isVisible()
  }

  /**
   * Get current active nav item
   */
  async getActiveNavItem() {
    const activeNav = this.page.locator('[aria-current="page"], .router-link-active, .q-tab--active')
    return await activeNav.textContent()
  }
}
