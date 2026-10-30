import { test, expect } from '@playwright/test';

const standardUser = {
  name: 'Broker Sync E2E User',
  email: `broker.sync.${Date.now()}@example.com`,
  password: 'Password123!',
};

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
  password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe('Broker Direct API Import UI E2E Test', () => {
  test.beforeAll(async ({ request }) => {
    const adminLoginResponse = await request.post('/api/v1/auth/login', {
      form: { username: adminUser.email, password: adminUser.password },
    });
    expect(adminLoginResponse.ok()).toBeTruthy();
    const { access_token } = await adminLoginResponse.json();
    const adminAuthHeaders = { Authorization: `Bearer ${access_token}` };

    await request.post('/api/v1/users/', {
      headers: adminAuthHeaders,
      data: { ...standardUser, is_admin: false },
    });
  });

  test('Navigate to Import page and verify Direct Broker API Sync card is visible', async ({ page }) => {
    // Login using standard workflow
    await page.goto('/');
    await page.getByLabel('Email address').fill(standardUser.email);
    await page.getByLabel('Password', { exact: true }).fill(standardUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // Navigate to Import page
    await page.getByRole('link', { name: 'Import' }).click();
    await expect(page.getByRole('heading', { name: 'Import Transactions' })).toBeVisible();

    // Check presence of Broker API Sync Card
    await expect(page.locator('text=Direct Broker API Sync (ICICI Breeze)')).toBeVisible();
    await expect(page.locator('text=ICICI Direct Breeze API')).toBeVisible();
    await expect(page.locator('text=Not Configured')).toBeVisible();
    await expect(page.locator('text=Please configure and authenticate ICICI Breeze under')).toBeVisible();

    // Verify clicking Profile / Settings redirects to /profile
    await page.getByRole('button', { name: 'Profile / Settings' }).click();
    await expect(page.getByRole('heading', { name: 'Profile & Settings' })).toBeVisible();
    await expect(page).toHaveURL(/.*\/profile/);
  });
});
