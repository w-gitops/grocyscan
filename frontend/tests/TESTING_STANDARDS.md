# Playwright UI Testing Standards

This document outlines the standards and best practices for writing UI tests in this project.

## Directory Structure

```
frontend/tests/
├── fixtures/           # Test fixtures (auth, common setup)
│   ├── auth.fixture.js
│   └── index.js
├── pages/              # Page Object Models
│   ├── base.page.js
│   ├── login.page.js
│   ├── scan.page.js
│   ├── products.page.js
│   ├── inventory.page.js
│   ├── locations.page.js
│   ├── jobs.page.js
│   ├── logs.page.js
│   ├── settings.page.js
│   ├── components/
│   │   └── navigation.js
│   └── index.js
├── specs/              # Test specifications
│   ├── auth.spec.js
│   ├── navigation.spec.js
│   ├── scan.spec.js
│   ├── products.spec.js
│   ├── locations.spec.js
│   ├── jobs.spec.js
│   ├── logs.spec.js
│   ├── settings.spec.js
│   ├── responsive.spec.js
│   └── theme.spec.js
├── smoke.spec.js       # Quick smoke tests
└── TESTING_STANDARDS.md
```

## Naming Conventions

### Test Files
- Spec files: `{feature}.spec.js`
- Page objects: `{page-name}.page.js`
- Fixtures: `{fixture-name}.fixture.js`

### Test Names
- Use descriptive names: `test('can create new location with freezer toggle')`
- Group related tests with `test.describe()`

## Selector Strategy

**Priority Order (use first available):**

1. **`data-testid` attributes** (preferred)
   ```javascript
   page.locator('[data-testid="login-submit"]')
   // Or via page object
   this.getByTestId('login-submit')
   ```

2. **Role selectors** (accessibility-based)
   ```javascript
   page.getByRole('button', { name: 'Sign In' })
   page.getByRole('heading', { name: 'Products' })
   ```

3. **Label selectors** (form inputs)
   ```javascript
   page.getByLabel('Username')
   page.getByLabel('Password')
   ```

4. **Text selectors** (visible text)
   ```javascript
   page.getByText('Sign in to continue')
   ```

5. **Placeholder selectors** (input hints)
   ```javascript
   page.getByPlaceholder('Search products...')
   ```

6. **CSS selectors** (last resort)
   ```javascript
   page.locator('.q-card .q-btn')
   ```

### Adding data-testid Attributes

When adding new UI elements, include `data-testid`:

```vue
<q-btn 
  label="Submit" 
  data-testid="form-submit-btn"
/>

<q-input
  v-model="name"
  label="Name"
  data-testid="product-name-input"
/>
```

**Naming convention for data-testid:**
- Use kebab-case
- Format: `{component}-{element}-{action/type}`
- Examples: `login-submit`, `product-edit-btn`, `scan-barcode-input`

## Page Object Model (POM)

### Creating a Page Object

```javascript
import { BasePage } from './base.page.js'

export class MyPage extends BasePage {
  constructor(page) {
    super(page)
    
    // Define selectors
    this.submitBtn = this.getByTestId('my-submit')
    this.nameInput = this.getByTestId('my-name-input')
    
    // Fallback selectors
    this.nameFallback = page.getByLabel('Name')
  }

  async goto() {
    await this.page.goto('/my-page')
  }

  async isOnPage() {
    return this.page.url().includes('/my-page')
  }

  // Page-specific actions
  async submitForm() {
    await this.submitBtn.click()
  }

  async fillName(name) {
    await this.nameInput.or(this.nameFallback).fill(name)
  }
}
```

### Using Fallback Selectors

Always provide fallbacks for critical elements:

```javascript
// In page object
this.primarySelector = this.getByTestId('my-button')
this.fallbackSelector = page.getByRole('button', { name: 'Submit' })

// Usage with .or()
async clickSubmit() {
  await this.primarySelector.or(this.fallbackSelector).click()
}
```

## Writing Tests

### Basic Test Structure

```javascript
import { test, expect } from '../fixtures/index.js'
import { MyPage } from '../pages/my.page.js'
import { LoginPage } from '../pages/login.page.js'

test.describe('My Feature', () => {
  test.beforeEach(async ({ page, request, baseURL }) => {
    // Check backend availability
    const health = await request.get(`${baseURL}/api/health`).catch(() => null)
    if (!health?.ok()) {
      test.skip(true, 'Backend not available')
    }

    // Login
    const loginPage = new LoginPage(page)
    await loginPage.navigate()
    await loginPage.login('admin', 'test')
  })

  test('descriptive test name', async ({ page }) => {
    const myPage = new MyPage(page)
    await myPage.navigate()
    
    // Actions
    await myPage.fillName('Test')
    await myPage.submitForm()
    
    // Assertions
    await expect(page.getByText('Success')).toBeVisible()
  })
})
```

### Test Best Practices

1. **Independence**: Each test should be independent
2. **Single Responsibility**: Test one thing per test
3. **Clear Assertions**: Use meaningful assertions
4. **Graceful Degradation**: Handle missing elements gracefully
5. **Backend Awareness**: Skip tests when backend unavailable

### Handling Async Operations

```javascript
// Wait for API response
await page.waitForResponse(response => 
  response.url().includes('/api/products') && response.ok()
)

// Wait for navigation
await expect(page).toHaveURL(/\/products/)

// Wait for element with timeout
await expect(page.getByTestId('result')).toBeVisible({ timeout: 5000 })
```

## Fixtures

### Authentication Fixture

```javascript
import { test, expect, TEST_CREDENTIALS } from '../fixtures/index.js'

// Use authenticated page
test('requires auth', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/protected')
})
```

### Custom Fixtures

Create reusable setup in `fixtures/`:

```javascript
import { test as base } from '@playwright/test'

export const test = base.extend({
  myFixture: async ({ page }, use) => {
    // Setup
    await page.goto('/setup')
    
    // Provide to test
    await use(page)
    
    // Cleanup
    await page.evaluate(() => localStorage.clear())
  }
})
```

## Running Tests

### Local Development

```bash
# Run all tests
npm run test:e2e

# Run specific test file
npx playwright test tests/specs/auth.spec.js

# Run with UI mode
npx playwright test --ui

# Run in headed mode
npx playwright test --headed

# Debug mode
npx playwright test --debug
```

### CI Environment

Tests run automatically on GitHub Actions. See `.github/workflows/ui-tests.yml`.

```bash
# CI-like run locally
CI=true npx playwright test
```

## Test Artifacts

- **Screenshots**: Auto-captured on failure
- **Videos**: Recorded in CI (configurable)
- **Traces**: Available for debugging
- **HTML Report**: Generated after test run

Location: `test-results/`

## Checklist for New Features

When adding tests for a new feature:

- [ ] Add `data-testid` attributes to Vue components
- [ ] Create Page Object in `pages/`
- [ ] Export from `pages/index.js`
- [ ] Create spec file in `specs/`
- [ ] Add tests for:
  - [ ] Page renders correctly
  - [ ] All interactive elements work
  - [ ] Form validation (if applicable)
  - [ ] Success/error states
  - [ ] Mobile responsiveness (if different behavior)
- [ ] Run tests locally
- [ ] Verify in CI

## Troubleshooting

### Common Issues

1. **Element not found**: Check if `data-testid` exists, use fallback selectors
2. **Timeout errors**: Increase timeout, check if backend is running
3. **Flaky tests**: Add proper waits, avoid timing-dependent assertions
4. **CI failures**: Check browser versions, review artifacts

### Debug Tips

```javascript
// Pause test execution
await page.pause()

// Take screenshot
await page.screenshot({ path: 'debug.png' })

// Log page content
console.log(await page.content())

// Slow down execution
test.use({ launchOptions: { slowMo: 500 } })
```
