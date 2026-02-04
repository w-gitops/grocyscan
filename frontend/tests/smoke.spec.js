import { test, expect } from '@playwright/test'

test('login screen renders', async ({ page }) => {
  await page.goto('/login')

  await expect(page.getByText('Sign in to continue')).toBeVisible()
  await expect(page.getByLabel('Username')).toBeVisible()
  await expect(page.getByLabel('Password')).toBeVisible()
  await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible()
})

test('unauthenticated user is redirected to login from /', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveURL(/\/login/)
  await expect(page.getByText('Sign in to continue')).toBeVisible()
})

test('unauthenticated user is redirected to login from /scan with redirect param', async ({ page }) => {
  await page.goto('/scan')
  await expect(page).toHaveURL(/\/login\?redirect=\/scan/)
  await expect(page.getByText('Sign in to continue')).toBeVisible()
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
