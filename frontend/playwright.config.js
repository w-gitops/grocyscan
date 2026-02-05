import { defineConfig, devices } from '@playwright/test'

const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:4173'
const useRemoteBaseUrl = Boolean(process.env.PLAYWRIGHT_BASE_URL)

export default defineConfig({
  testDir: './tests',
  
  // Test matching pattern - include specs and smoke tests
  testMatch: ['**/*.spec.js'],
  
  // Timeouts
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  
  // Retries - more in CI for stability
  retries: process.env.CI ? 2 : 0,
  
  // Parallel execution - limit workers in CI for stability
  workers: process.env.CI ? 2 : undefined,
  fullyParallel: true,
  
  // Reporter configuration
  reporter: process.env.CI
    ? [
        ['list'],
        ['html', { outputFolder: 'playwright-report', open: 'never' }],
        ['json', { outputFile: 'test-results/results.json' }],
        ['junit', { outputFile: 'test-results/junit.xml' }]
      ]
    : [
        ['html', { open: 'on-failure' }]
      ],
  
  // Output directories
  outputDir: 'test-results',
  
  // Global settings
  use: {
    baseURL,
    
    // Capture on failure for debugging
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    
    // Action timeout
    actionTimeout: 10_000,
    
    // Navigation timeout
    navigationTimeout: 15_000,
  },
  
  // Browser projects
  projects: [
    // Desktop Chrome - primary target
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
      },
    },
    
    // Mobile Chrome - for responsive tests
    {
      name: 'mobile-chrome',
      use: {
        ...devices['Pixel 5'],
      },
      // Only run responsive tests on mobile
      testMatch: ['**/responsive.spec.js'],
    },
    
    // Desktop Firefox - secondary browser (optional, enable as needed)
    // {
    //   name: 'firefox',
    //   use: {
    //     ...devices['Desktop Firefox'],
    //   },
    // },
    
    // Desktop Safari - secondary browser (optional, enable as needed)
    // {
    //   name: 'webkit',
    //   use: {
    //     ...devices['Desktop Safari'],
    //   },
    // },
  ],
  
  // Web server configuration
  webServer: useRemoteBaseUrl
    ? undefined
    : {
        command: 'npm run build && npm run preview -- --host 0.0.0.0 --port 4173',
        url: baseURL,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
        stdout: 'pipe',
        stderr: 'pipe',
      },
  
  // Metadata for reports
  metadata: {
    project: 'GrocyScan',
    environment: process.env.CI ? 'CI' : 'local',
  },
})
