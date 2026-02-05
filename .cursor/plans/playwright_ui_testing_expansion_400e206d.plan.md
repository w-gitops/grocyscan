---
name: Playwright UI Testing Expansion
overview: Establish comprehensive Playwright E2E testing infrastructure with page object model, fixtures, standards documentation, and preparation for self-hosted GitHub Actions runner.
todos:
  - id: infrastructure
    content: Create test directory structure, fixtures (auth.fixture.js), and base page object model pattern
    status: completed
  - id: data-testid
    content: Add data-testid attributes to Vue components (LoginPage, ScanPage, ProductsPage, LocationsPage, SettingsPage, MainLayout)
    status: completed
  - id: page-objects
    content: Create page object classes for all 8 pages (login, scan, products, inventory, locations, jobs, logs, settings)
    status: completed
  - id: core-tests
    content: Write tests for auth flow, navigation, and scan page (highest priority user flows)
    status: completed
  - id: feature-tests
    content: Write tests for Products, Locations, Settings (all 5 tabs), Jobs, and Logs pages
    status: completed
  - id: advanced-tests
    content: Add responsive design tests (mobile/tablet/desktop) and theme tests (light/dark/auto)
    status: completed
  - id: standards-doc
    content: Create TESTING_STANDARDS.md with patterns, conventions, and checklist for new feature tests
    status: completed
  - id: config-updates
    content: Update playwright.config.js with mobile project, JSON reporter, and optimized CI settings
    status: completed
  - id: self-hosted-prep
    content: Create SELF_HOSTED_RUNNER.md documentation and update workflow with browser caching and runner label support
    status: completed
isProject: false
---

# Comprehensive Playwright UI Testing Plan

## Current State Analysis

**Existing setup:**

- 4 smoke tests in `[frontend/tests/smoke.spec.js](frontend/tests/smoke.spec.js)` (login rendering, redirects, basic login flow)
- Basic `[playwright.config.js](frontend/playwright.config.js)` with Chromium, failure screenshots/traces/video
- CI workflow in `[.github/workflows/ui-tests.yml](.github/workflows/ui-tests.yml)` with full backend services
- Manual BrowserMCP testing plan with 100+ test cases documented

**Gaps:**

- No test fixtures or utilities
- No page object model (POM)
- No `data-testid` attributes in Vue components
- Only smoke tests, no feature coverage
- No standards documentation for new test development
- Self-hosted runner not configured

---

## Phase 1: Test Infrastructure Foundation

### 1.1 Directory Structure

```
frontend/tests/
  fixtures/
    auth.fixture.js       # Login helpers, authenticated context
    base.fixture.js       # Extended test with all fixtures
  pages/
    login.page.js         # LoginPage POM
    scan.page.js          # ScanPage POM
    products.page.js      # ProductsPage POM
    inventory.page.js     # InventoryPage POM
    locations.page.js     # LocationsPage POM
    jobs.page.js          # JobsPage POM
    logs.page.js          # LogsPage POM
    settings.page.js      # SettingsPage POM
    components/
      navigation.js       # Header/mobile nav component
      product-dialog.js   # Product review dialog
      date-picker.js      # Touch date picker
  specs/
    auth.spec.js          # Authentication tests
    scan.spec.js          # Scan page tests
    products.spec.js      # Products page tests
    inventory.spec.js     # Inventory page tests
    locations.spec.js     # Locations page tests
    jobs.spec.js          # Jobs page tests
    logs.spec.js          # Logs page tests
    settings.spec.js      # Settings page tests (all 5 tabs)
    navigation.spec.js    # Navigation tests
    responsive.spec.js    # Responsive design tests
  smoke.spec.js           # Keep existing smoke tests
```

### 1.2 Base Fixtures (`[fixtures/auth.fixture.js](frontend/tests/fixtures/auth.fixture.js)`)

```javascript
import { test as base } from '@playwright/test'

export const test = base.extend({
  // Authenticated page - logs in before test
  authenticatedPage: async ({ page, request }, use) => {
    // Login via API to get session cookie
    await request.post('/api/auth/login', {
      data: { username: 'admin', password: 'test' }
    })
    await use(page)
  },
  
  // Storage state for reuse across tests
  storageState: async ({ browser }, use) => {
    const context = await browser.newContext()
    const page = await context.newPage()
    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('test')
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL(/\/scan/)
    const state = await context.storageState()
    await context.close()
    await use(state)
  }
})

export { expect } from '@playwright/test'
```

### 1.3 Page Object Model Example (`[pages/scan.page.js](frontend/tests/pages/scan.page.js)`)

```javascript
export class ScanPage {
  constructor(page) {
    this.page = page
    this.barcodeInput = page.getByTestId('barcode-input')
    this.submitButton = page.getByTestId('scan-submit')
    this.cameraButton = page.getByTestId('camera-button')
    this.feedbackArea = page.getByTestId('scan-feedback')
    this.recentScans = page.getByTestId('recent-scans')
    this.locationSelector = page.getByTestId('location-selector')
  }

  async goto() {
    await this.page.goto('/scan')
  }

  async scanBarcode(barcode) {
    await this.barcodeInput.fill(barcode)
    await this.submitButton.click()
  }

  async waitForFeedback(type) {
    await this.feedbackArea.waitFor({ state: 'visible' })
  }
}
```

---

## Phase 2: Add `data-testid` Attributes to Vue Components

### 2.1 Priority Components

Add `data-testid` attributes to these Vue files for reliable selectors:


| Component  | File                                                        | Key Elements                                                      |
| ---------- | ----------------------------------------------------------- | ----------------------------------------------------------------- |
| Login      | `[LoginPage.vue](frontend/src/pages/LoginPage.vue)`         | form, username, password, submit, error                           |
| Scan       | `[ScanPage.vue](frontend/src/pages/ScanPage.vue)`           | barcode-input, scan-submit, camera-button, feedback, recent-scans |
| Products   | `[ProductsPage.vue](frontend/src/pages/ProductsPage.vue)`   | search, add-button, product-list, product-card                    |
| Locations  | `[LocationsPage.vue](frontend/src/pages/LocationsPage.vue)` | add-button, location-list, sync-button                            |
| Settings   | `[SettingsPage.vue](frontend/src/pages/SettingsPage.vue)`   | tab-grocy, tab-llm, tab-lookup, tab-scanning, tab-ui              |
| Navigation | `[MainLayout.vue](frontend/src/layouts/MainLayout.vue)`     | nav-scan, nav-products, nav-locations, mobile-drawer              |


### 2.2 Naming Convention

```
data-testid="[component]-[element]"

Examples:
- data-testid="login-username"
- data-testid="scan-barcode-input"
- data-testid="products-search"
- data-testid="settings-tab-grocy"
```

---

## Phase 3: Comprehensive Test Coverage

### 3.1 Test Mapping (from BrowserMCP plan)


| Area           | Test File            | Coverage                                          |
| -------------- | -------------------- | ------------------------------------------------- |
| Authentication | `auth.spec.js`       | AUTH-01 to AUTH-07 (login, validation, redirects) |
| Navigation     | `navigation.spec.js` | NAV-01 to NAV-12 (header + mobile nav)            |
| Scan Page      | `scan.spec.js`       | SCAN-01 to SCAN-10 (input, camera, feedback)      |
| Products Page  | `products.spec.js`   | PROD-01 to PROD-06 (search, filter, CRUD)         |
| Locations Page | `locations.spec.js`  | LOC-01 to LOC-10 (CRUD, sync)                     |
| Jobs Page      | `jobs.spec.js`       | JOB-01 to JOB-07 (stats, filtering)               |
| Logs Page      | `logs.spec.js`       | LOG-01 to LOG-07 (filter, search, actions)        |
| Settings       | `settings.spec.js`   | SET-G01 to SET-U06 (all 5 tabs)                   |
| Components     | `components.spec.js` | CMP-* (scanner, review dialog, date picker)       |
| Responsive     | `responsive.spec.js` | RSP-01 to RSP-04 (375px, 768px, 1280px)           |
| Theme          | `theme.spec.js`      | THM-01 to THM-05 (light/dark/auto)                |


### 3.2 Test Example (Scan Page)

```javascript
// frontend/tests/specs/scan.spec.js
import { test, expect } from '../fixtures/auth.fixture.js'
import { ScanPage } from '../pages/scan.page.js'

test.describe('Scan Page', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    const scanPage = new ScanPage(authenticatedPage)
    await scanPage.goto()
  })

  test('displays barcode input and submit button', async ({ page }) => {
    await expect(page.getByTestId('barcode-input')).toBeVisible()
    await expect(page.getByTestId('scan-submit')).toBeVisible()
  })

  test('shows feedback on barcode scan', async ({ page }) => {
    const scanPage = new ScanPage(page)
    await scanPage.scanBarcode('4006381333931')
    await expect(scanPage.feedbackArea).toBeVisible()
  })

  test('opens camera dialog', async ({ page }) => {
    await page.getByTestId('camera-button').click()
    await expect(page.getByRole('dialog')).toBeVisible()
  })
})
```

---

## Phase 4: Standards Documentation

Create `[frontend/tests/TESTING_STANDARDS.md](frontend/tests/TESTING_STANDARDS.md)`:

### Key Sections

- Test file naming: `[feature].spec.js`
- Selector priority: `data-testid` > `getByRole` > `getByLabel` > `getByText`
- Page Object Model requirements
- Fixture usage patterns
- CI integration guidelines
- How to run tests locally vs remote
- Screenshot/trace artifacts handling
- Adding tests for new features checklist

---

## Phase 5: Playwright Configuration Enhancements

Update `[playwright.config.js](frontend/playwright.config.js)`:

```javascript
export default defineConfig({
  testDir: './tests',
  testMatch: ['**/*.spec.js'],
  timeout: 30_000,
  expect: { timeout: 5_000 },
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: process.env.CI
    ? [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }], ['json', { outputFile: 'test-results.json' }]]
    : 'html',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:4173',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['iPhone 13'] } },
  ],
  // ...webServer config
})
```

**Additions:**

- Mobile project for responsive testing
- JSON reporter for CI parsing
- Increased retries in CI (2 instead of 1)
- Explicit worker count for CI

---

## Phase 6: Self-Hosted Runner Preparation

### 6.1 Runner Requirements Document

Create `[.github/SELF_HOSTED_RUNNER.md](.github/SELF_HOSTED_RUNNER.md)`:

- Hardware requirements (2+ CPU, 4GB+ RAM)
- Software dependencies (Docker, Node.js 20, Python 3.12)
- Browser installation (`npx playwright install --with-deps`)
- Network access requirements (localhost services)
- Security considerations

### 6.2 Workflow Label Preparation

Update `[ui-tests.yml](.github/workflows/ui-tests.yml)` with conditional runner selection:

```yaml
jobs:
  ui:
    runs-on: ${{ github.event.inputs.runner || 'ubuntu-latest' }}
    # OR for self-hosted:
    # runs-on: [self-hosted, linux, x64, playwright]
```

### 6.3 Browser Caching for Self-Hosted

```yaml
- name: Cache Playwright browsers
  uses: actions/cache@v4
  with:
    path: ~/.cache/ms-playwright
    key: playwright-${{ runner.os }}-${{ hashFiles('frontend/package-lock.json') }}
```

---

## Implementation Order

1. **Infrastructure** - Create directory structure, fixtures, base POM
2. `**data-testid**` - Add attributes to Vue components (high-impact)
3. **Page Objects** - Create POMs for all 8 pages
4. **Core Tests** - Auth, Navigation, Scan page (most critical flows)
5. **Feature Tests** - Products, Locations, Settings, Jobs, Logs
6. **Advanced Tests** - Responsive, Theme, Components
7. **Standards Doc** - Document patterns for future development
8. **Self-Hosted Prep** - Runner docs, workflow updates, caching

---

## Success Metrics

- Test count: 4 (current) to 60+ tests
- Page coverage: 1/8 pages to 8/8 pages
- CI run time: Target under 5 minutes
- Flakiness: Less than 2% flaky tests
- Standards: All new PRs include tests for UI changes

