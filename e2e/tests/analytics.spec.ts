import { test, expect, Page } from '@playwright/test';
import { faker } from '@faker-js/faker';
import { createPortfolio, createTransaction, createAsset } from '../utils';

test.describe.configure({ mode: 'parallel' });

const standardUser = {
  email: faker.internet.email(),
  password: 'password',
};

// Helper to get a date in the past in YYYY-MM-DD format
const getPastDateISO = (daysAgo: number): string => {
  const date = new Date();
  date.setDate(date.getDate() - daysAgo);
  return date.toISOString().split('T')[0];
};

test.describe('Advanced Analytics E2E Flow', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    const apiContext = await browser.newContext();
    const api = apiContext.request;
    const standardUserCreateResponse = await api.post('/api/v1/users/', {
      data: { ...standardUser, is_admin: false },
    });
    expect(standardUserCreateResponse.ok()).toBeTruthy();
    await apiContext.dispose();
  });

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    // Login as the standard user before each test
    await page.goto('/');
    await page.getByLabel('Email address').fill(standardUser.email);
    await page.getByLabel('Password').fill(standardUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await page.waitForURL('**/dashboard', { timeout: 30000 });
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('should display advanced analytics for a portfolio', async ({ page }) => {
    const portfolioName = `Analytics Test Portfolio ${faker.string.uuid()}`;
    const assetName = 'MSFT';

    // 1. Create a portfolio
    const portfolio = await createPortfolio(page.request, portfolioName, 'USD');
    await page.goto(`/portfolio/${portfolio.id}`);
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // 2. Add transactions to create a history
    const asset = await createAsset(page.request, assetName, 'Microsoft Corporation', 'STOCK', 'USD', 'NASDAQ');
    // BUY 10 shares
    await createTransaction(page.request, portfolio.id, asset.id, 'buy', 10, 200, '2023-01-01');
    // SELL 5 shares
    await createTransaction(page.request, portfolio.id, asset.id, 'sell', 5, 220, '2023-06-01');

    await page.reload();

    // Verify the holding quantity was updated from 10 to 5
    const holdingRow = page.locator('.card', { hasText: 'Holdings' }).getByRole('row', { name: /MSFT/ });
    await expect(holdingRow.getByRole('cell', { name: '5', exact: true })).toBeVisible();

    // 3. Verify Analytics Card is visible and displays data
    const analyticsCard = page.locator('.card', { hasText: 'Advanced Analytics' });
    await expect(analyticsCard).toBeVisible();

    // Check for XIRR - value can fluctuate, so just check for format
    const xirrValue = analyticsCard.locator('p', { hasText: 'XIRR' }).locator('xpath=..//p[2]');
    await expect(xirrValue).toContainText(/%$/); // Check that it ends with a percentage sign

    // Check for Sharpe Ratio - value can fluctuate, so just check for format
    const sharpeRatioValue = analyticsCard.locator('div:has-text("Sharpe Ratio")').locator('p').last();
    await expect(sharpeRatioValue).not.toContainText("N/A");
  });

  test('should display correct asset-level XIRR in the holding detail modal', async ({ page }) => {
    const portfolioName = `Asset XIRR Test Portfolio ${faker.string.uuid()}`;
    const assetTicker = 'XIRRTEST';
    const assetName = 'XIRR Test Company';

    // 1. Create a portfolio and asset
    const portfolio = await createPortfolio(page.request, portfolioName, 'USD');
    const asset = await createAsset(page.request, assetTicker, assetName, 'Stock', 'INR', 'NSE');

    await page.goto(`/portfolio/${portfolio.id}`);
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // 2. Add transactions with specific dates for XIRR calculation
    // BUY 10 shares @ 100, 1 year ago
    await createTransaction(page.request, portfolio.id, asset.id, 'buy', 10, 100, getPastDateISO(365));
    // SELL 5 shares @ 120, 6 months ago
    await createTransaction(page.request, portfolio.id, asset.id, 'sell', 5, 120, getPastDateISO(182));

    await page.reload();

    // 3. Open the holding detail modal
    const holdingRow = page.locator('.card', { hasText: 'Holdings' }).getByRole('row', { name: new RegExp(assetTicker) });
    await holdingRow.click();

    // 4. Verify the XIRR values
    const modal = page.getByRole('dialog');
    await expect(modal).toBeVisible();

    // Wait for the data to load before checking the values
    await expect(modal.getByText('Loading transactions...')).not.toBeVisible({ timeout: 10000 });

    const unrealizedXirrContainer = modal.getByText('Unrealized XIRR').locator('xpath=..');
    await expect(unrealizedXirrContainer.getByText('8.00%')).toBeVisible();
  });
});