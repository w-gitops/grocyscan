/**
 * Settings Page Object
 */
import { BasePage } from './base.page.js'

export class SettingsPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Page container
    this.pageContainer = this.getByTestId('settings-page')
    
    // Tabs
    this.tabsContainer = this.getByTestId('settings-tabs')
    this.grocyTab = this.getByTestId('settings-tab-grocy')
    this.llmTab = this.getByTestId('settings-tab-llm')
    this.lookupTab = this.getByTestId('settings-tab-lookup')
    this.scanningTab = this.getByTestId('settings-tab-scanning')
    this.uiTab = this.getByTestId('settings-tab-ui')
    
    // Grocy panel
    this.grocyApiUrl = this.getByTestId('grocy-api-url')
    this.grocyApiKey = this.getByTestId('grocy-api-key')
    this.grocyWebUrl = this.getByTestId('grocy-web-url')
    this.grocyTestBtn = this.getByTestId('grocy-test-btn')
    this.grocySaveBtn = this.getByTestId('grocy-save-btn')
    this.grocyStatus = this.getByTestId('grocy-status')
    
    // LLM panel
    this.llmProviderPreset = this.getByTestId('llm-provider-preset')
    this.llmApiUrl = this.getByTestId('llm-api-url')
    this.llmApiKey = this.getByTestId('llm-api-key')
    this.llmModel = this.getByTestId('llm-model')
    this.llmSaveBtn = this.getByTestId('llm-save-btn')
    
    // Lookup panel
    this.lookupStrategy = this.getByTestId('lookup-strategy')
    this.offEnabled = this.getByTestId('lookup-off-enabled')
    this.goupcEnabled = this.getByTestId('lookup-goupc-enabled')
    this.upcitemdbEnabled = this.getByTestId('lookup-upcitemdb-enabled')
    this.braveEnabled = this.getByTestId('lookup-brave-enabled')
    this.lookupSaveBtn = this.getByTestId('lookup-save-btn')
    
    // Scanning panel
    this.scanningAutoAdd = this.getByTestId('scanning-auto-add')
    this.scanningFuzzyThreshold = this.getByTestId('scanning-fuzzy-threshold')
    this.scanningDefaultUnit = this.getByTestId('scanning-default-unit')
    this.scanningKioskMode = this.getByTestId('scanning-kiosk-mode')
    this.scanningSaveBtn = this.getByTestId('scanning-save-btn')
    
    // UI panel
    this.uiKioskMode = this.getByTestId('ui-kiosk-mode')
    this.uiSaveBtn = this.getByTestId('ui-save-btn')
    
    // Fallbacks
    this.pageTitleFallback = page.getByText('Settings')
  }

  async goto() {
    await this.page.goto('/settings')
  }

  async isOnPage() {
    return this.page.url().includes('/settings')
  }

  /**
   * Switch to tab
   */
  async switchToTab(tabName) {
    const tabMap = {
      grocy: this.grocyTab,
      llm: this.llmTab,
      lookup: this.lookupTab,
      scanning: this.scanningTab,
      ui: this.uiTab
    }
    const tab = tabMap[tabName]
    if (tab) {
      await tab.click()
    } else {
      // Fallback to clicking by label
      await this.page.getByRole('tab', { name: new RegExp(tabName, 'i') }).click()
    }
  }

  /**
   * Configure Grocy connection
   */
  async configureGrocy({ apiUrl, apiKey, webUrl }) {
    await this.switchToTab('grocy')
    if (apiUrl) {
      const input = this.grocyApiUrl.or(this.page.getByLabel('API URL'))
      await input.fill(apiUrl)
    }
    if (apiKey) {
      const input = this.grocyApiKey.or(this.page.getByLabel('API Key'))
      await input.fill(apiKey)
    }
    if (webUrl) {
      const input = this.grocyWebUrl.or(this.page.getByLabel('Web URL'))
      await input.fill(webUrl)
    }
  }

  /**
   * Test Grocy connection
   */
  async testGrocyConnection() {
    await this.grocyTestBtn.or(this.page.getByRole('button', { name: /test connection/i })).click()
  }

  /**
   * Save Grocy settings
   */
  async saveGrocySettings() {
    await this.grocySaveBtn.or(this.page.getByRole('button', { name: 'Save' }).first()).click()
  }

  /**
   * Configure LLM
   */
  async configureLLM({ provider, apiUrl, apiKey, model }) {
    await this.switchToTab('llm')
    if (provider) {
      await this.llmProviderPreset.or(this.page.getByLabel('Provider Preset')).click()
      await this.page.getByRole('option', { name: provider }).click()
    }
    if (apiUrl) await this.llmApiUrl.or(this.page.locator('input[label="API URL"]')).fill(apiUrl)
    if (apiKey) await this.llmApiKey.or(this.page.locator('input[type="password"]')).fill(apiKey)
    if (model) await this.llmModel.or(this.page.getByLabel('Model')).fill(model)
  }

  /**
   * Save LLM settings
   */
  async saveLLMSettings() {
    await this.llmSaveBtn.or(this.page.getByRole('button', { name: 'Save' })).click()
  }

  /**
   * Get current tab name
   */
  async getCurrentTab() {
    const activeTab = this.page.locator('.q-tab--active')
    return activeTab.textContent()
  }

  /**
   * Check if Grocy connection is successful
   */
  async isGrocyConnected() {
    const status = this.grocyStatus.or(this.page.locator('.text-green:has-text("Connected")'))
    return status.isVisible()
  }
}
