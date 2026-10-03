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
    // Login
    await page.goto('/login');
    await page.fill('input[type="email"]', standardUser.email);
    await page.fill('input[type="password"]', standardUser.password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');

    // Navigate to Import page
    await page.goto('/import');

    // Check presence of Broker API Sync Card
    await expect(page.locator('text=Direct Broker API Sync (NFR12)')).toBeVisible();
    await expect(page.locator('text=Zerodha Kite API')).toBeVisible();
    await expect(page.locator('text=ICICI Breeze API')).toBeVisible();
    await expect(page.locator('text=Not Configured')).toBeVisible();
  });
});
