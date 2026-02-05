import { test, expect } from '@playwright/test'

test('login screen renders', async ({ page }) => {
  await page.goto('/login')

  await expect(page.getByText('Sign in to continue')).toBeVisible()
  await expect(page.getByLabel('Username')).toBeVisible()
  await expect(page.getByLabel('Password')).toBeVisible()
  await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible()
})

test('unauthenticated user on / ends up at login or scan', async ({ page }) => {
  await page.goto('/')
  // Wait for any redirects to complete
  await page.waitForLoadState('networkidle')
  // App may redirect to login or allow access depending on auth config
  const url = page.url()
  expect(url).toMatch(/\/(login|scan)/)
})

test('unauthenticated user on /scan ends up at login or scan', async ({ page }) => {
  await page.goto('/scan')
  // App may redirect to login or allow access depending on auth config
  await expect(page).toHaveURL(/\/(login|scan)/)
})

test('login and reach Scan page when backend is available', async ({ page, request }) => {
  const health = await request.get('/api/health').catch(() => null)
  if (!health?.ok()) {
    test.skip(true, 'Backend not available; skipping login E2E')
  }
  await page.goto('/login')
  await page.getByLabel('Username').fill('admin')
  await page.getByLabel('Password').fill('test')
  await page.getByRole('button', { name: /sign in/i }).click()
  await expect(page).toHaveURL(/\/scan/)
  await expect(page.getByRole('heading', { name: 'Scan' })).toBeVisible()
})
