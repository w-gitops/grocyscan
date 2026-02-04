import { defineConfig, devices } from '@playwright/test'

const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:4173'
const useRemoteBaseUrl = Boolean(process.env.PLAYWRIGHT_BASE_URL)

export default defineConfig({
  testDir: './tests',
  
  // Match all .spec.js files (including in subdirectories like specs/)
  testMatch: '**/*.spec.js',
  
  // Timeouts
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  
  // Retries - more in CI for stability
  retries: process.env.CI ? 2 : 0,
  
  // Parallel execution
  workers: process.env.CI ? 2 : undefined,
  fullyParallel: true,
  
  // Reporters
  reporter: process.env.CI
    ? [
        ['list'],
        ['html', { outputFolder: 'playwright-report', open: 'never' }],
        ['json', { outputFile: 'test-results/results.json' }],
      ]
    : [['html', { open: 'on-failure' }]],
  
  // Output directory
  outputDir: 'test-results',
  
  use: {
    baseURL,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10_000,
  },
  
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
      },
    },
    // Mobile project for responsive tests
    {
      name: 'mobile',
      use: {
        ...devices['Pixel 5'],
      },
      testMatch: '**/responsive.spec.js',
    },
  ],
  
  webServer: useRemoteBaseUrl
    ? undefined
    : {
        command: 'npm run build && npm run preview -- --host 0.0.0.0 --port 4173',
        url: baseURL,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
})
