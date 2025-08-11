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

// Helper to get a date in the past in YYYY-MM-DD format
const getPastDateISO = (daysAgo: number): string => {
  const date = new Date();
  date.setDate(date.getDate() - daysAgo);
  return date.toISOString().split('T')[0];
};

test.describe.serial('Advanced Analytics E2E Flow', () => {
  test.beforeAll(async ({ request }) => {
    // The global setup has already created the admin user.
    // We just need to log in as admin to create our test-specific standard user.
    const adminLoginResponse = await request.post('/api/v1/auth/login', {
      form: { username: adminUser.email, password: adminUser.password },
    });
    expect(adminLoginResponse.ok()).toBeTruthy();
    const { access_token } = await adminLoginResponse.json();
    const adminAuthHeaders = { Authorization: `Bearer ${access_token}` };

    // Create the standard user needed for this test file
    const standardUserCreateResponse = await request.post('/api/v1/users/', {
      headers: adminAuthHeaders,
      data: { ...standardUser, is_admin: false },
    });
    expect(standardUserCreateResponse.ok()).toBeTruthy();
  });

  test.beforeEach(async ({ page }) => {
    // Login as the standard user before each test
    await page.goto('/');
    await page.getByLabel('Email address').fill(standardUser.email);
    await page.getByLabel('Password').fill(standardUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should display advanced analytics for a portfolio', async ({ page }) => {
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
    await expect(page.locator('.card', { hasText: 'Holdings' }).getByRole('row', { name: /MSFT/ })).toBeVisible({ timeout: 15000 });

    // SELL 5 shares
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Type', { exact: true }).selectOption('SELL');
    await page.getByLabel('Asset').pressSequentially(assetName);
    const listItem = page.locator(`li:has-text("${assetName}")`);
    await expect(listItem).toBeVisible();
    await listItem.click();
    await page.getByLabel('Quantity').fill('5');
    await page.getByLabel('Price per Unit').fill('220');
    await page.getByLabel('Date').fill('2023-06-01');
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    // Verify the holding quantity was updated from 10 to 5
    const holdingRow = page.locator('.card', { hasText: 'Holdings' }).getByRole('row', { name: /MSFT/ });
    await expect(holdingRow.getByRole('cell', { name: '5', exact: true })).toBeVisible();

    // 3. Verify Analytics Card is visible and displays data
    const analyticsCard = page.locator('.card', { hasText: 'Advanced Analytics' });
    await expect(analyticsCard).toBeVisible();

    // Use data-testid for unambiguous selection
    const realizedXirrValue = analyticsCard.getByTestId('realized-xirr-container').locator('p.text-xl');
    await expect(realizedXirrValue).toContainText(/%$/);

    const unrealizedXirrValue = analyticsCard.getByTestId('unrealized-xirr-container').locator('p.text-xl');
    await expect(unrealizedXirrValue).toContainText(/%$/);

    const sharpeRatioValue = analyticsCard.getByTestId('sharpe-ratio-container').locator('p.text-xl');
    await expect(sharpeRatioValue).not.toBeEmpty();
  });

  test('should display correct asset-level XIRR in the holding detail modal', async ({ page }) => {
    const portfolioName = `Asset XIRR Test Portfolio ${Date.now()}`;
    const assetTicker = 'XIRRTEST';

    // 1. Create a portfolio
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // 2. Add transactions with specific dates for XIRR calculation
    // BUY 10 shares @ 100, 1 year ago
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Type', { exact: true }).selectOption('BUY');
    await page.getByLabel('Asset').pressSequentially(assetTicker);
    const createAssetButton = page.getByRole('button', { name: `Create Asset "${assetTicker}"` });
    await expect(createAssetButton).toBeVisible();
    await createAssetButton.click();
    await page.getByLabel('Quantity').fill('10');
    await page.getByLabel('Price per Unit').fill('100');
    await page.getByLabel('Date').fill(getPastDateISO(365));
    await page.getByRole('button', { name: 'Save Transaction' }).click();
    await expect(page.locator('.card', { hasText: 'Holdings' }).getByRole('row', { name: new RegExp(assetTicker) })).toBeVisible();

    // SELL 5 shares @ 120, 6 months ago
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Type', { exact: true }).selectOption('SELL');
    await page.getByLabel('Asset').pressSequentially(assetTicker);
    await page.waitForResponse(response => response.url().includes('/api/v1/assets/lookup'));
    const listItem = page.locator(`li:has-text("${assetTicker}")`);
    await expect(listItem).toBeVisible();
    await listItem.click();
    await page.getByLabel('Quantity').fill('5');
    await page.getByLabel('Price per Unit').fill('120');
    await page.getByLabel('Date').fill(getPastDateISO(182));
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    // 3. Open the holding detail modal
    const holdingRow = page.locator('.card', { hasText: 'Holdings' }).getByRole('row', { name: new RegExp(assetTicker) });
    await holdingRow.click();

    // 4. Verify the XIRR values
    const modal = page.getByRole('dialog');
    await expect(modal).toBeVisible();

    // Wait for the data to load before checking the values
    await expect(modal.getByText('Loading transactions...')).not.toBeVisible({ timeout: 10000 });

    // Wait for the analytics to load and verify the values
    const realizedXirrContainer = modal.getByText('Realized XIRR').locator('xpath=..');
    await expect(realizedXirrContainer.getByText('43.86%')).toBeVisible({ timeout: 10000 });

    const unrealizedXirrContainer = modal.getByText('Unrealized XIRR').locator('xpath=..');
    await expect(unrealizedXirrContainer.getByText('30.00%')).toBeVisible();
  });
});
