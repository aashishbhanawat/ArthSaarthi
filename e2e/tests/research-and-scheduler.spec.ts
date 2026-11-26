import { test, expect } from '@playwright/test';

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
  password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe('Market Research, Scheduler & Admin Maintenance E2E', () => {
  let pageErrors: Error[] = [];
  let serverErrors: string[] = [];

  test.beforeEach(async ({ page }) => {
    pageErrors = [];
    serverErrors = [];
    page.on('pageerror', (err) => pageErrors.push(err));
    page.on('response', (res) => {
      if (res.status() >= 500) {
        serverErrors.push(`${res.status()} ${res.url()}`);
      }
    });

    await page.goto('/');
    await page.getByLabel('Email address').fill(adminUser.email);
    await page.getByLabel('Password', { exact: true }).fill(adminUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test.afterEach(() => {
    expect(pageErrors, `Uncaught page errors: ${pageErrors.map((e) => e.message).join('; ')}`).toHaveLength(0);
    expect(serverErrors, `HTTP 5xx responses: ${serverErrors.join('; ')}`).toHaveLength(0);
  });

  test('should navigate Research & News feed and switch category tabs', async ({ page }) => {
    const researchLink = page.getByRole('link', { name: 'Research & News' });
    if (!(await researchLink.isVisible())) {
      await page.getByRole('button', { name: 'Markets & Research' }).click();
    }
    await researchLink.click();

    await expect(page).toHaveURL(/.*\/research/);
    await expect(page.getByRole('heading', { name: 'Market & Research' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Holding Intelligence & Research' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sync Now' })).toBeVisible();

    for (const tabLabel of ['News & Pulse', 'Broker Targets', 'Earnings Concalls', 'Quarterly Results', 'All Insights']) {
      await page.getByRole('button', { name: new RegExp(tabLabel) }).click();
    }
  });

  test('should display AI Model Management and Scheduler Dashboard in System Maintenance', async ({ page }) => {
    const maintenanceLink = page.getByRole('link', { name: 'System Maintenance' });
    if (!(await maintenanceLink.isVisible())) {
      await page.getByRole('button', { name: 'Administration' }).click();
    }
    await maintenanceLink.click();

    await expect(page).toHaveURL(/.*\/admin\/maintenance/);
    await expect(page.getByRole('heading', { name: 'Shared Edge ML Models' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Automated Tasks' })).toBeVisible();

    // Open Activity History modal
    await page.getByRole('button', { name: 'Activity History' }).click();
    await expect(page.getByRole('button', { name: 'Close' }).or(page.locator('button:has-text("Close")')).first()).toBeVisible();
  });

  test('should render FMV Management and Symbol Aliases admin pages cleanly', async ({ page }) => {
    const fmvLink = page.getByRole('link', { name: 'FMV Management' });
    if (!(await fmvLink.isVisible())) {
      await page.getByRole('button', { name: 'Administration' }).click();
    }
    await fmvLink.click();
    await expect(page).toHaveURL(/.*\/admin\/fmv/);

    const aliasesLink = page.getByRole('link', { name: 'Symbol Aliases' });
    if (!(await aliasesLink.isVisible())) {
      await page.getByRole('button', { name: 'Administration' }).click();
    }
    await aliasesLink.click();
    await expect(page).toHaveURL(/.*\/admin\/aliases/);
  });
});
