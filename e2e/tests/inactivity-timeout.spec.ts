import { test, expect } from '@playwright/test';

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
  password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe('Inactivity Timeout', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByLabel('Email address').fill(adminUser.email);
    await page.getByLabel('Password').fill(adminUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test.afterEach(async ({ page }) => {
    await page.evaluate(() => {
      sessionStorage.removeItem('e2e_inactivity_timeout');
      sessionStorage.removeItem('e2e_modal_countdown_seconds');
    });
  });

  test('should show session timeout modal and log out user on inactivity', async ({ page }) => {
    await page.evaluate(() => {
      sessionStorage.setItem('e2e_inactivity_timeout', '3000'); // 3 seconds
      sessionStorage.setItem('e2e_modal_countdown_seconds', '3'); // 3 seconds
    });

    // Reload the page to apply the new timeout
    await page.reload();

    await expect(page.locator('text=Session Timeout')).toBeVisible({ timeout: 8000 });
    await expect(page.locator('text=You will be logged out in 3 seconds due to inactivity.')).toBeVisible();

    // Wait for the countdown to finish and the user to be logged out
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible({ timeout: 8000 });
  });

  test('should allow user to extend session', async ({ page }) => {
    await page.evaluate(() => {
      sessionStorage.setItem('e2e_inactivity_timeout', '3000'); // 3 seconds
    });

    // Reload the page to apply the new timeout
    await page.reload();

    await expect(page.locator('text=Session Timeout')).toBeVisible({ timeout: 8000 });
    await page.click('text=Stay Logged In');

    await expect(page.locator('text=Session Timeout')).not.toBeVisible();
  });
});
