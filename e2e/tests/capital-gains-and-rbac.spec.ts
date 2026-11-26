import { test, expect } from '@playwright/test';

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
  password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe('Capital Gains, RBAC & Profile Tabs E2E', () => {
  let pageErrors: Error[] = [];
  let serverErrors: string[] = [];
  const standardUser = {
    full_name: 'RBAC E2E User',
    email: `rbac.e2e.${Date.now()}@example.com`,
    password: 'Password123!',
  };

  test.beforeAll(async ({ request }) => {
    const loginRes = await request.post('/api/v1/auth/login', {
      form: { username: adminUser.email, password: adminUser.password },
    });
    expect(loginRes.ok()).toBeTruthy();
    const { access_token } = await loginRes.json();

    const createRes = await request.post('/api/v1/users/', {
      headers: { Authorization: `Bearer ${access_token}` },
      data: { ...standardUser, is_admin: false },
    });
    expect(createRes.ok()).toBeTruthy();
  });

  test.beforeEach(async ({ page }) => {
    pageErrors = [];
    serverErrors = [];
    page.on('pageerror', (err) => pageErrors.push(err));
    page.on('response', (res) => {
      if (res.status() >= 500) {
        serverErrors.push(`${res.status()} ${res.url()}`);
      }
    });
  });

  test.afterEach(() => {
    expect(pageErrors, `Uncaught page errors: ${pageErrors.map((e) => e.message).join('; ')}`).toHaveLength(0);
    expect(serverErrors, `HTTP 5xx responses: ${serverErrors.join('; ')}`).toHaveLength(0);
  });

  test('should navigate Capital Gains, Schedule FA, and Dividend Report tabs', async ({ page }) => {
    await page.goto('/');
    await page.getByLabel('Email address').fill(adminUser.email);
    await page.getByLabel('Password', { exact: true }).fill(adminUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    const cgLink = page.getByRole('link', { name: 'Capital Gains' });
    if (!(await cgLink.isVisible())) {
      await page.getByRole('button', { name: 'Tax & Income' }).click();
    }
    await cgLink.click();

    await expect(page).toHaveURL(/.*\/capital-gains/);
    await expect(page.getByRole('heading', { name: 'Tax Reports' })).toBeVisible();
    await expect(page.locator('#fy-select')).toBeVisible();
    await expect(page.locator('#slab-rate')).toBeVisible();

    await page.getByRole('button', { name: 'Schedule FA (Foreign Assets)' }).click();
    await page.getByRole('button', { name: 'Dividend Report' }).click();
    await page.getByRole('button', { name: 'Capital Gains' }).click();
  });

  test('should enforce non-admin RBAC and render Profile & Settings tabs', async ({ page }) => {
    await page.goto('/');
    await page.getByLabel('Email address').fill(standardUser.email);
    await page.getByLabel('Password', { exact: true }).fill(standardUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // Non-admin should not see Administration menu
    await expect(page.getByRole('button', { name: 'Administration' })).not.toBeVisible();

    // Direct navigation to admin routes should not render admin pages
    await page.goto('/admin/users');
    await expect(page.getByRole('heading', { name: 'User Management' })).not.toBeVisible();

    // Navigate to Profile & Settings and verify tabs
    await page.getByRole('link', { name: /Profile/ }).click();
    await expect(page).toHaveURL(/.*\/profile/);

    await page.getByRole('button', { name: /Risk Profile/ }).click();
    await page.getByRole('button', { name: /Broker Integrations/ }).click();
    await expect(page.getByText('Broker API Integration')).toBeVisible();
    await page.getByRole('button', { name: /Data & System/ }).click();
  });
});
