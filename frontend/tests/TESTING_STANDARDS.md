# GrocyScan Playwright Testing Standards

This document establishes the standards and best practices for writing E2E tests with Playwright in the GrocyScan project.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Directory Structure](#directory-structure)
3. [Test File Naming](#test-file-naming)
4. [Selector Strategy](#selector-strategy)
5. [Page Object Model](#page-object-model)
6. [Fixtures](#fixtures)
7. [Writing Tests](#writing-tests)
8. [Running Tests](#running-tests)
9. [CI Integration](#ci-integration)
10. [Checklist for New Features](#checklist-for-new-features)

---

## Quick Start

```bash
# Install dependencies
cd frontend
npm install

# Install Playwright browsers
npx playwright install

# Run all tests (requires backend)
npm run test:e2e

# Run tests against remote server
PLAYWRIGHT_BASE_URL=https://grocyscan.example.com npm run test:e2e

# Run specific test file
npx playwright test tests/specs/auth.spec.js

# Run tests with UI mode
npx playwright test --ui
```

---

## Directory Structure

```
frontend/tests/
├── fixtures/               # Test fixtures and helpers
│   ├── auth.fixture.js     # Authentication fixtures
│   └── index.js            # Central export
├── pages/                  # Page Object Models
│   ├── base.page.js        # Base page class
│   ├── login.page.js       # Login page
│   ├── scan.page.js        # Scan page
│   ├── products.page.js    # Products page
│   ├── inventory.page.js   # Inventory page
│   ├── locations.page.js   # Locations page
│   ├── jobs.page.js        # Jobs page
│   ├── logs.page.js        # Logs page
│   ├── settings.page.js    # Settings page
│   ├── components/         # Reusable component objects
│   │   └── navigation.js   # Navigation component
│   └── index.js            # Central export
├── specs/                  # Test specifications
│   ├── auth.spec.js        # Authentication tests
│   ├── navigation.spec.js  # Navigation tests
│   ├── scan.spec.js        # Scan page tests
│   ├── products.spec.js    # Products page tests
│   ├── locations.spec.js   # Locations page tests
│   ├── settings.spec.js    # Settings page tests
│   ├── jobs.spec.js        # Jobs page tests
│   ├── logs.spec.js        # Logs page tests
│   ├── responsive.spec.js  # Responsive design tests
│   └── theme.spec.js       # Theme tests
├── smoke.spec.js           # Smoke tests (fast, critical path)
└── TESTING_STANDARDS.md    # This file
```

---

## Test File Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature tests | `[feature].spec.js` | `auth.spec.js`, `scan.spec.js` |
| Component tests | `[component].spec.js` | `navigation.spec.js` |
| Page objects | `[page].page.js` | `login.page.js` |
| Fixtures | `[name].fixture.js` | `auth.fixture.js` |

---

## Selector Strategy

### Priority Order (Most to Least Preferred)

1. **`data-testid`** - Most stable, test-specific
2. **`getByRole`** - Accessible, semantic
3. **`getByLabel`** - For form inputs
4. **`getByText`** - For static content
5. **CSS selectors** - Last resort

### data-testid Naming Convention

```
data-testid="[component]-[element]"

Examples:
- data-testid="login-username"
- data-testid="scan-barcode-input"
- data-testid="products-search"
- data-testid="settings-tab-grocy"
- data-testid="nav-scan"
- data-testid="mobile-nav-products"
```

### Examples

```javascript
// GOOD - data-testid (preferred)
page.getByTestId('scan-barcode-input')

// GOOD - Role-based (accessible)
page.getByRole('button', { name: /sign in/i })

// GOOD - Label (form inputs)
page.getByLabel('Username')

// OK - Text (static content)
page.getByText('Sign in to continue')

// AVOID - CSS selectors (brittle)
page.locator('.q-input__control')
```

### Adding data-testid to Components

When adding new Vue components, include `data-testid` attributes:

```vue
<template>
  <q-input
    v-model="value"
    label="Search"
    data-testid="products-search"
  />
  <q-btn
    label="Submit"
    data-testid="products-submit"
    @click="onSubmit"
  />
</template>
```

---

## Page Object Model

### Base Page Class

All page objects extend `BasePage`:

```javascript
import { BasePage } from './base.page.js'

export class MyPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Define locators
    this.myInput = page.getByTestId('my-input')
    this.myButton = page.getByTestId('my-button')
  }

  async goto() {
    await this.page.goto('/my-page')
  }

  async isOnPage() {
    return this.page.url().includes('/my-page')
  }

  // Page-specific methods
  async fillForm(data) {
    await this.myInput.fill(data)
  }
}
```

### Page Object Guidelines

1. **Locators in constructor** - Define all locators in the constructor
2. **Fallback selectors** - Provide fallbacks for components without `data-testid`
3. **Encapsulate interactions** - Methods should represent user actions
4. **No assertions** - Page objects should not contain assertions

```javascript
// GOOD - Method represents user action
async login(username, password) {
  await this.usernameInput.fill(username)
  await this.passwordInput.fill(password)
  await this.submitButton.click()
}

// BAD - Assertion in page object
async login(username, password) {
  await this.usernameInput.fill(username)
  expect(this.usernameInput).toHaveValue(username) // Don't do this
}
```

---

## Fixtures

### Authentication Fixture

Use the auth fixture for tests that require login:

```javascript
import { test, expect } from '../fixtures/auth.fixture.js'

test('authenticated test', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/scan')
  // User is already logged in
})
```

### Available Fixtures

| Fixture | Description |
|---------|-------------|
| `authenticatedPage` | Page with session cookie from API login |
| `authStorageState` | Storage state for reuse across tests |
| `authedContext` | Browser context with saved auth |
| `authedPage` | Page from authenticated context |

### Skipping Tests When Backend Unavailable

```javascript
test('requires backend', async ({ page, request, baseURL }) => {
  const health = await request.get(`${baseURL}/api/health`).catch(() => null)
  if (!health?.ok()) {
    test.skip(true, 'Backend not available')
  }
  
  // Test code here
})
```

---

## Writing Tests

### Test Structure

```javascript
import { test, expect } from '../fixtures/auth.fixture.js'
import { ScanPage } from '../pages/scan.page.js'

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page, request, baseURL }) => {
    // Skip if backend unavailable
    const health = await request.get(`${baseURL}/api/health`).catch(() => null)
    if (!health?.ok()) {
      test.skip(true, 'Backend not available')
    }

    // Login
    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('test')
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL(/\/scan/)
  })

  test.describe('Sub-feature', () => {
    test('should do something', async ({ page }) => {
      const scanPage = new ScanPage(page)
      await scanPage.goto()
      
      await scanPage.enterBarcode('1234567890')
      await expect(scanPage.barcodeInput).toHaveValue('1234567890')
    })
  })
})
```

### Best Practices

1. **One assertion per test** (when practical)
2. **Descriptive test names** - Use full sentences
3. **Arrange-Act-Assert** pattern
4. **Avoid sleep** - Use waitFor* methods instead
5. **Handle conditional UI** - Check if elements exist before interacting

```javascript
// GOOD - Wait for element
await expect(page.getByTestId('loading')).toBeHidden()
await expect(page.getByTestId('content')).toBeVisible()

// BAD - Fixed sleep
await page.waitForTimeout(5000)

// OK - Short timeout for animations
await page.waitForTimeout(500)
```

### Handling Conditional Elements

```javascript
// Check if dialog exists before interacting
const dialog = page.getByTestId('product-review-dialog')
if (await dialog.isVisible().catch(() => false)) {
  await page.getByTestId('product-review-cancel').click()
}
```

---

## Running Tests

### Local Development

```bash
# Run all tests
npm run test:e2e

# Run specific file
npx playwright test tests/specs/auth.spec.js

# Run tests matching pattern
npx playwright test -g "login"

# Run with UI mode
npx playwright test --ui

# Run with headed browser
npx playwright test --headed

# Debug mode
npx playwright test --debug
```

### Against Remote Server

```bash
PLAYWRIGHT_BASE_URL=https://grocyscan.example.com npm run test:e2e
```

### View Reports

```bash
npx playwright show-report
```

---

## CI Integration

### GitHub Actions

Tests run automatically on:
- PRs to `dev` and `main` branches
- Manual workflow dispatch

### Artifacts

After CI runs, download:
- `playwright-report/` - HTML report
- `e2e-run.log` - Test output

Use the expansion scripts:
```bash
# PowerShell
.\scripts\expand-playwright-report.ps1

# Bash
./scripts/expand-playwright-report.sh
```

### Test Credentials

CI uses:
- Username: `admin`
- Password: `test`

These are set via `AUTH_USERNAME` and `AUTH_PASSWORD_HASH` environment variables.

---

## Checklist for New Features

When adding a new feature, follow this checklist:

### 1. Add data-testid Attributes

- [ ] Add `data-testid` to all interactive elements
- [ ] Follow naming convention: `[component]-[element]`
- [ ] Add to form inputs, buttons, dialogs, lists

### 2. Create/Update Page Object

- [ ] Add locators for new elements
- [ ] Add methods for user interactions
- [ ] Export from `pages/index.js`

### 3. Write Tests

- [ ] Create new spec file or add to existing
- [ ] Test happy path
- [ ] Test error states
- [ ] Test edge cases
- [ ] Test at different viewports (if UI changes)

### 4. Update Documentation

- [ ] Add test mapping to this file if new feature area
- [ ] Document any special test setup required

### 5. Verify

- [ ] Run tests locally
- [ ] Ensure tests pass in CI
- [ ] Check for flakiness (run 3x)

---

## Test Mapping Reference

| Feature Area | Test File | BrowserMCP IDs |
|-------------|-----------|----------------|
| Authentication | `auth.spec.js` | AUTH-01 to AUTH-07 |
| Navigation | `navigation.spec.js` | NAV-01 to NAV-12 |
| Scan Page | `scan.spec.js` | SCAN-01 to SCAN-10 |
| Products Page | `products.spec.js` | PROD-01 to PROD-06 |
| Locations Page | `locations.spec.js` | LOC-01 to LOC-10 |
| Jobs Page | `jobs.spec.js` | JOB-01 to JOB-07 |
| Logs Page | `logs.spec.js` | LOG-01 to LOG-07 |
| Settings | `settings.spec.js` | SET-G01 to SET-U06 |
| Responsive | `responsive.spec.js` | RSP-01 to RSP-04 |
| Theme | `theme.spec.js` | THM-01 to THM-05 |

---

## Troubleshooting

### Common Issues

**Tests fail with "Backend not available"**
- Ensure the backend is running on port 3334
- Or set `PLAYWRIGHT_BASE_URL` to a running instance

**Element not found**
- Check if element has `data-testid`
- Verify selector in browser DevTools
- May need to wait for element to appear

**Flaky tests**
- Add explicit waits for async operations
- Check for race conditions
- Ensure test isolation

**Timeout errors**
- Increase timeout in config or test
- Check if element is actually visible
- May need to scroll element into view

### Debug Commands

```javascript
// Pause execution
await page.pause()

// Take screenshot
await page.screenshot({ path: 'debug.png' })

// Log page content
console.log(await page.content())

// Log element text
console.log(await element.textContent())
```

---

## Resources

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Page Object Model Pattern](https://playwright.dev/docs/pom)
- [Locators Guide](https://playwright.dev/docs/locators)
- [Test Assertions](https://playwright.dev/docs/test-assertions)
- [CI Integration](https://playwright.dev/docs/ci)
