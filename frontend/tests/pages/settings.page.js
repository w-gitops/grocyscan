/**
 * Settings Page Object
 * 
 * Encapsulates all interactions with the settings page (all 5 tabs).
 */
import { BasePage } from './base.page.js'

export class SettingsPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Tab navigation
    this.grocyTab = page.getByTestId('settings-tab-grocy')
    this.llmTab = page.getByTestId('settings-tab-llm')
    this.lookupTab = page.getByTestId('settings-tab-lookup')
    this.scanningTab = page.getByTestId('settings-tab-scanning')
    this.uiTab = page.getByTestId('settings-tab-ui')
    
    // Fallback tab selectors
    this.grocyTabFallback = page.getByRole('tab', { name: /grocy/i })
    this.llmTabFallback = page.getByRole('tab', { name: /llm/i })
    this.lookupTabFallback = page.getByRole('tab', { name: /lookup/i })
    this.scanningTabFallback = page.getByRole('tab', { name: /scanning/i })
    this.uiTabFallback = page.getByRole('tab', { name: /ui/i })
    
    // === GROCY TAB ===
    this.grocyApiUrl = page.getByTestId('grocy-api-url')
    this.grocyApiKey = page.getByTestId('grocy-api-key')
    this.grocyWebUrl = page.getByTestId('grocy-web-url')
    this.grocyTestButton = page.getByTestId('grocy-test-connection')
    this.grocyTestStatus = page.getByTestId('grocy-test-status')
    this.grocySaveButton = page.getByTestId('grocy-save-button')
    
    // === LLM TAB ===
    this.llmProviderPreset = page.getByTestId('llm-provider-preset')
    this.llmApiUrl = page.getByTestId('llm-api-url')
    this.llmApiKey = page.getByTestId('llm-api-key')
    this.llmModel = page.getByTestId('llm-model')
    this.llmTestButton = page.getByTestId('llm-test-connection')
    this.llmSaveButton = page.getByTestId('llm-save-button')
    
    // === LOOKUP TAB ===
    this.lookupStrategy = page.getByTestId('lookup-strategy')
    this.openFoodFactsToggle = page.getByTestId('lookup-openfoodfacts-toggle')
    this.goUpcToggle = page.getByTestId('lookup-goupc-toggle')
    this.goUpcApiKey = page.getByTestId('lookup-goupc-apikey')
    this.upcItemDbToggle = page.getByTestId('lookup-upcitemdb-toggle')
    this.braveSearchToggle = page.getByTestId('lookup-bravesearch-toggle')
    this.braveSearchFallbackToggle = page.getByTestId('lookup-bravesearch-fallback')
    this.lookupTestButtons = page.getByTestId('lookup-test-provider')
    this.lookupSaveButton = page.getByTestId('lookup-save-button')
    
    // === SCANNING TAB ===
    this.autoAddToggle = page.getByTestId('scanning-auto-add')
    this.kioskModeToggle = page.getByTestId('scanning-kiosk-mode')
    this.fuzzyThreshold = page.getByTestId('scanning-fuzzy-threshold')
    this.defaultQuantityUnit = page.getByTestId('scanning-default-quantity-unit')
    this.scanningSaveButton = page.getByTestId('scanning-save-button')
    
    // === UI TAB ===
    this.lightThemeButton = page.getByTestId('ui-theme-light')
    this.darkThemeButton = page.getByTestId('ui-theme-dark')
    this.autoThemeButton = page.getByTestId('ui-theme-auto')
    this.saveThemeButton = page.getByTestId('ui-save-theme')
    
    // Page elements
    this.pageTitle = page.getByRole('heading', { name: 'Settings' })
    this.saveNotification = page.getByText(/saved|success/i)
  }

  async goto() {
    await this.page.goto('/settings')
  }

  async isOnPage() {
    return this.page.url().includes('/settings')
  }

  async waitForLoad() {
    await this.pageTitle.waitFor({ state: 'visible' })
  }

  // === TAB NAVIGATION ===

  async switchToTab(tabName) {
    const tabs = {
      grocy: [this.grocyTab, this.grocyTabFallback],
      llm: [this.llmTab, this.llmTabFallback],
      lookup: [this.lookupTab, this.lookupTabFallback],
      scanning: [this.scanningTab, this.scanningTabFallback],
      ui: [this.uiTab, this.uiTabFallback]
    }
    
    const [primary, fallback] = tabs[tabName]
    const tab = await primary.isVisible().catch(() => false) ? primary : fallback
    await tab.click()
  }

  async getCurrentTab() {
    // Find the active tab
    const activeTab = this.page.locator('[role="tab"][aria-selected="true"], .q-tab--active')
    const text = await activeTab.textContent()
    return text.toLowerCase()
  }

  // === GROCY TAB METHODS ===

  async fillGrocySettings({ apiUrl, apiKey, webUrl }) {
    await this.switchToTab('grocy')
    
    if (apiUrl) {
      const field = await this.grocyApiUrl.isVisible().catch(() => false)
        ? this.grocyApiUrl
        : this.page.getByLabel(/api url/i)
      await field.fill(apiUrl)
    }
    if (apiKey) {
      const field = await this.grocyApiKey.isVisible().catch(() => false)
        ? this.grocyApiKey
        : this.page.getByLabel(/api key/i)
      await field.fill(apiKey)
    }
    if (webUrl) {
      const field = await this.grocyWebUrl.isVisible().catch(() => false)
        ? this.grocyWebUrl
        : this.page.getByLabel(/web url/i)
      await field.fill(webUrl)
    }
  }

  async testGrocyConnection() {
    const btn = await this.grocyTestButton.isVisible().catch(() => false)
      ? this.grocyTestButton
      : this.page.getByRole('button', { name: /test connection/i })
    await btn.click()
  }

  async saveGrocySettings() {
    const btn = await this.grocySaveButton.isVisible().catch(() => false)
      ? this.grocySaveButton
      : this.page.getByRole('button', { name: /save/i })
    await btn.click()
  }

  // === LLM TAB METHODS ===

  async selectLlmPreset(preset) {
    await this.switchToTab('llm')
    const selector = await this.llmProviderPreset.isVisible().catch(() => false)
      ? this.llmProviderPreset
      : this.page.getByLabel(/provider|preset/i)
    await selector.click()
    await this.page.getByRole('option', { name: new RegExp(preset, 'i') }).click()
  }

  async fillLlmSettings({ apiUrl, apiKey, model }) {
    await this.switchToTab('llm')
    
    if (apiUrl) {
      const field = await this.llmApiUrl.isVisible().catch(() => false)
        ? this.llmApiUrl
        : this.page.getByLabel(/api url/i)
      await field.fill(apiUrl)
    }
    if (apiKey) {
      const field = await this.llmApiKey.isVisible().catch(() => false)
        ? this.llmApiKey
        : this.page.getByLabel(/api key/i)
      await field.fill(apiKey)
    }
    if (model) {
      const field = await this.llmModel.isVisible().catch(() => false)
        ? this.llmModel
        : this.page.getByLabel(/model/i)
      await field.fill(model)
    }
  }

  async testLlmConnection() {
    const btn = await this.llmTestButton.isVisible().catch(() => false)
      ? this.llmTestButton
      : this.page.getByRole('button', { name: /test/i })
    await btn.click()
  }

  // === LOOKUP TAB METHODS ===

  async setLookupStrategy(strategy) {
    await this.switchToTab('lookup')
    const selector = await this.lookupStrategy.isVisible().catch(() => false)
      ? this.lookupStrategy
      : this.page.getByLabel(/strategy/i)
    await selector.click()
    await this.page.getByRole('option', { name: new RegExp(strategy, 'i') }).click()
  }

  async toggleLookupProvider(provider, enabled) {
    await this.switchToTab('lookup')
    const toggles = {
      openfoodfacts: this.openFoodFactsToggle,
      goupc: this.goUpcToggle,
      upcitemdb: this.upcItemDbToggle,
      bravesearch: this.braveSearchToggle
    }
    
    const toggle = toggles[provider.toLowerCase()] || this.page.getByLabel(new RegExp(provider, 'i'))
    const isChecked = await toggle.isChecked()
    if (isChecked !== enabled) {
      await toggle.click()
    }
  }

  async testLookupProvider(provider) {
    await this.switchToTab('lookup')
    const testBtn = this.page.getByTestId(`lookup-test-${provider.toLowerCase()}`)
    const btn = await testBtn.isVisible().catch(() => false)
      ? testBtn
      : this.page.locator(`button`).filter({ hasText: new RegExp(`test.*${provider}`, 'i') })
    await btn.click()
  }

  // === SCANNING TAB METHODS ===

  async toggleAutoAdd(enabled) {
    await this.switchToTab('scanning')
    const toggle = await this.autoAddToggle.isVisible().catch(() => false)
      ? this.autoAddToggle
      : this.page.getByLabel(/auto.?add/i)
    const isChecked = await toggle.isChecked()
    if (isChecked !== enabled) {
      await toggle.click()
    }
  }

  async toggleKioskMode(enabled) {
    await this.switchToTab('scanning')
    const toggle = await this.kioskModeToggle.isVisible().catch(() => false)
      ? this.kioskModeToggle
      : this.page.getByLabel(/kiosk/i)
    const isChecked = await toggle.isChecked()
    if (isChecked !== enabled) {
      await toggle.click()
    }
  }

  async setFuzzyThreshold(value) {
    await this.switchToTab('scanning')
    const field = await this.fuzzyThreshold.isVisible().catch(() => false)
      ? this.fuzzyThreshold
      : this.page.getByLabel(/threshold/i)
    await field.fill(String(value))
  }

  // === UI TAB METHODS ===

  async setTheme(theme) {
    await this.switchToTab('ui')
    const buttons = {
      light: this.lightThemeButton,
      dark: this.darkThemeButton,
      auto: this.autoThemeButton
    }
    
    const btn = await buttons[theme].isVisible().catch(() => false)
      ? buttons[theme]
      : this.page.getByRole('button', { name: new RegExp(theme, 'i') })
    await btn.click()
  }

  async saveTheme() {
    const btn = await this.saveThemeButton.isVisible().catch(() => false)
      ? this.saveThemeButton
      : this.page.getByRole('button', { name: /save theme/i })
    await btn.click()
  }

  // === GENERAL METHODS ===

  async saveCurrentTab() {
    const saveBtn = this.page.getByRole('button', { name: /save/i }).first()
    await saveBtn.click()
  }

  async waitForSaveConfirmation() {
    await this.saveNotification.waitFor({ state: 'visible' })
  }
}
