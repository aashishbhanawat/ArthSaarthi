import { test, expect, Page } from '@playwright/test';

const standardUser = {
  name: 'Analytics User E2E',
  email: `analytics.e2e.${Date.now()}@example.com`,
  password: 'Password123!',
};

const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('Advanced Analytics E2E Flow', () => {
  let page: Page;

  test.beforeAll(async ({ request }) => {
    // 1. Reset the database
    const resetResponse = await request.post('/api/v1/testing/reset-db');
    expect(resetResponse.status()).toBe(204);

    // 2. Create Admin User via API for a faster, more reliable setup
    const adminSetupResponse = await request.post('/api/v1/auth/setup', {
      data: {
        full_name: 'Admin User',
        email: adminUser.email,
        password: adminUser.password,
      },
    });
    expect(adminSetupResponse.ok()).toBeTruthy();

    // 3. Login as Admin to get token for creating the standard user
    const adminLoginResponse = await request.post('/api/v1/auth/login', {
      form: { username: adminUser.email, password: adminUser.password },
    });
    expect(adminLoginResponse.ok()).toBeTruthy();
    const { access_token } = await adminLoginResponse.json();
    const adminAuthHeaders = { Authorization: `Bearer ${access_token}` };

    // 4. Create Standard User via API (as Admin)
    const standardUserCreateResponse = await request.post('/api/v1/users/', {
      headers: adminAuthHeaders,
      data: { ...standardUser, is_admin: false },
    });
    expect(standardUserCreateResponse.ok()).toBeTruthy();
  });

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    // Login as the standard user before each test
    await page.goto('/');
    await page.getByLabel('Email address').fill(standardUser.email);
    await page.getByLabel('Password').fill(standardUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('should display advanced analytics for a portfolio', async () => {
    const portfolioName = `Analytics Test Portfolio ${Date.now()}`;
    const assetName = 'MSFT';

    // 1. Create a portfolio
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // 2. Add transactions to create a history
    // BUY 10 shares
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Type', { exact: true }).selectOption('BUY');
    await page.getByLabel('Asset').pressSequentially(assetName);
    const createAssetButton = page.getByRole('button', { name: `Create Asset "${assetName}"` });
    await expect(createAssetButton).toBeVisible();
    await createAssetButton.click();
    await page.getByLabel('Quantity').fill('10');
    await page.getByLabel('Price per Unit').fill('200');
    await page.getByLabel('Date').fill('2023-01-01');
    await page.getByRole('button', { name: 'Save Transaction' }).click();
    await expect(page.getByRole('row', { name: /MSFT.*BUY.*10/ })).toBeVisible();

    // SELL 5 shares
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Type', { exact: true }).selectOption('SELL');
    await page.getByLabel('Asset').pressSequentially(assetName);
    await page.waitForResponse(response => response.url().includes('/api/v1/assets/lookup'));
    const listItem = page.locator(`li:has-text("${assetName}")`);
    await expect(listItem).toBeVisible();
    await listItem.click();
    await page.getByLabel('Quantity').fill('5');
    await page.getByLabel('Price per Unit').fill('220');
    await page.getByLabel('Date').fill('2023-06-01');
    await page.getByRole('button', { name: 'Save Transaction' }).click();
    await expect(page.getByRole('row', { name: /MSFT.*SELL.*5/ })).toBeVisible();

    // 3. Verify Analytics Card is visible and displays data
    const analyticsCard = page.locator('.card', { hasText: 'Advanced Analytics' });
    await expect(analyticsCard).toBeVisible();

    // Check for XIRR - value can fluctuate, so just check for format
    const xirrValue = analyticsCard.locator('p', { hasText: 'XIRR' }).locator('xpath=..//p[2]');
    await expect(xirrValue).toContainText(/%$/); // Check that it ends with a percentage sign

    // Check for Sharpe Ratio - value can fluctuate, so just check for format
    const sharpeRatioValue = analyticsCard.locator('p', { hasText: 'Sharpe Ratio' }).locator('xpath=..//p[2]');
    await expect(sharpeRatioValue).not.toBeEmpty(); // Check that it's not empty
  });
});
