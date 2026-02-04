import { test, expect } from '@playwright/test'

test('login screen renders', async ({ page }) => {
  await page.goto('/login')

  await expect(page.getByText('Sign in to continue')).toBeVisible()
  await expect(page.getByLabel('Username')).toBeVisible()
  await expect(page.getByLabel('Password')).toBeVisible()
  await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible()
})
