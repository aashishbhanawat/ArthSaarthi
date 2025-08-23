import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should allow a user to log in', async ({ page }) => {
    await page.goto('/login');

    // Wait for the setup to complete and the login form to be visible
    await page.waitForSelector('input[name="username"]');

    // Use a test user that is created in the global setup
    await page.fill('input[name="username"]', 'testuser@example.com');
    await page.fill('input[name="password"]', 'a-secure-password');

    await page.click('button[type="submit"]');

    await page.waitForURL('/dashboard', { timeout: 10000 });
    await expect(page).toHaveURL('/dashboard');
  });
});
