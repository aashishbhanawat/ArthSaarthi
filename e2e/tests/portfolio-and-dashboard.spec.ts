import { test, expect, Page } from '@playwright/test';
import { faker } from '@faker-js/faker';
import { createPortfolio, createTransaction, createAsset } from '../utils';

test.describe.configure({ mode: 'parallel' });

const standardUser = {
  email: faker.internet.email(),
  password: 'password',
};

const adminUser = {
  email: process.env.VITE_TEST_ADMIN_EMAIL || 'admin@example.com',
  password: process.env.VITE_TEST_ADMIN_PASSWORD || 'AdminPass123!',
};

test.describe('Portfolio and Dashboard E2E Flow', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    const apiContext = await browser.newContext();
    const api = apiContext.request;

    // Create Standard User via API
    const standardUserCreateResponse = await api.post('/api/v1/users/', {
      data: { email: standardUser.email, password: standardUser.password, is_admin: false },
    });
    expect(standardUserCreateResponse.ok()).toBeTruthy();

    // Login as admin to create assets
    const adminLoginResponse = await api.post('/api/v1/auth/token', {
      form: { username: adminUser.email, password: adminUser.password },
    });
    expect(adminLoginResponse.ok()).toBeTruthy();
    const { access_token } = await adminLoginResponse.json();
    const adminAuthHeaders = { Authorization: `Bearer ${access_token}` };

    // Create necessary assets for the import test (as Admin)
    const assetsToCreate = [
      { ticker_symbol: 'AAPL', name: 'Apple Inc.', asset_type: 'Stock', currency: 'USD', exchange: 'NASDAQ' },
      { ticker_symbol: 'GOOGL', name: 'Alphabet Inc.', asset_type: 'Stock', currency: 'USD', exchange: 'NASDAQ' },
    ];

    for (const asset of assetsToCreate) {
        const assetCreateResponse = await api.post('/api/v1/assets/', {
            headers: adminAuthHeaders,
            data: asset,
        });
        expect(assetCreateResponse.ok()).toBeTruthy();
    }
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

  test('should allow a user to create, view, and delete a portfolio', async ({ page }) => {
    const portfolioName = `My E2E Portfolio ${faker.string.uuid()}`;

    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();

    // Verify creation and navigation to detail page
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible({ timeout: 10000 });

    // Go back and delete
    await page.getByRole('link', { name: 'Back to Portfolios' }).click();

    const portfolioRow = page.locator('.card', { hasText: new RegExp(portfolioName) });
    await expect(portfolioRow).toBeVisible();
    await portfolioRow.getByRole('button', { name: 'Delete' }).click();

    await expect(page.getByRole('dialog')).toBeVisible(); // Verify the modal is open
    // Scope the search to the dialog to click the correct "Delete" button
    await page.getByRole('dialog').getByRole('button', { name: 'Delete' }).click();

    // Verify deletion
    await expect(page.getByRole('heading', { name: 'Portfolios' })).toBeVisible();
    await expect(portfolioRow).not.toBeVisible();
  });

  test('should allow a user to add various types of transactions', async ({ page }) => {
    const portfolioName = `My Transaction Portfolio ${faker.string.uuid()}`;
    const newAssetName = 'GOOGL';

    // 1. Create a portfolio to hold transactions
    const portfolio = await createPortfolio(page.request, portfolioName, 'USD');
    await page.goto(`/portfolio/${portfolio.id}`);

    // 2. Add a BUY transaction for a NEW asset
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Type', { exact: true }).selectOption('BUY');
    await page.getByLabel('Asset').pressSequentially(newAssetName, { delay: 100 });
    await page.waitForResponse('/api/v1/assets/lookup**');
    await page.locator(`li:has-text("${newAssetName}")`).click();
    await page.getByLabel('Quantity').fill('10');
    await page.getByLabel('Price per Unit').fill('150.00');
    await page.getByLabel('Date').fill('2023-01-15');
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    // Verify the new holding appears in the HoldingsTable
    const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
    await expect(holdingsTable).toBeVisible();
    const googlRow = holdingsTable.getByRole('row', { name: /GOOGL/ });
    await expect(googlRow).toBeVisible();
    await expect(googlRow.getByRole('cell', { name: '10', exact: true })).toBeVisible(); // Quantity

    // 3. Add a SELL transaction for the same asset
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Type', { exact: true }).selectOption('SELL');
    await page.getByLabel('Asset').pressSequentially(newAssetName, { delay: 100 });
    await page.waitForResponse(response => response.url().includes('/api/v1/assets/lookup'));
    const listItem = page.locator(`li:has-text("${newAssetName}")`);
    await expect(listItem).toBeVisible();
    await listItem.click();
    await page.getByLabel('Quantity').fill('5');
    await page.getByLabel('Price per Unit').fill('160.00');
    await page.getByLabel('Date').fill('2023-01-16');
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    // Verify the holding quantity is updated
    await expect(holdingsTable).toBeVisible();
    await expect(googlRow).toBeVisible();
    await expect(googlRow.getByRole('cell', { name: '5', exact: true })).toBeVisible(); // Quantity
  });

  test('should prevent a user from creating an invalid SELL transaction', async ({ page }) => {
    const portfolioName = `Invalid Sell Portfolio ${faker.string.uuid()}`;
    const assetName = 'AAPL'; // Use a different asset to avoid test contamination

    // 1. Create a portfolio
    const portfolio = await createPortfolio(page.request, portfolioName, 'USD');
    await page.goto(`/portfolio/${portfolio.id}`);

    // 2. Add a BUY transaction for 10 shares
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Type', { exact: true }).selectOption('BUY');
    await page.getByLabel('Asset').pressSequentially(assetName, { delay: 100 });
    await page.waitForResponse('/api/v1/assets/lookup**');
    await page.locator(`li:has-text("${assetName}")`).click();
    await page.getByLabel('Quantity').fill('10');
    await page.getByLabel('Price per Unit').fill('175.00');
    await page.getByLabel('Date').fill('2023-01-15');
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    // Verify the new holding appears in the HoldingsTable
    const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
    await expect(holdingsTable).toBeVisible();
    const aaplRow = holdingsTable.getByRole('row', { name: /AAPL/ });
    await expect(aaplRow).toBeVisible();
    await expect(aaplRow.getByRole('cell', { name: '10', exact: true })).toBeVisible(); // Quantity

    // 3. Attempt to SELL 20 shares (which is more than owned)
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Type', { exact: true }).selectOption('SELL');
    await page.getByLabel('Asset').pressSequentially(assetName, { delay: 100 });
    await page.waitForResponse((response) => response.url().includes('/api/v1/assets/lookup'));
    const listItemSell = page.locator(`li:has-text("${assetName}")`);
    await expect(listItemSell).toBeVisible();
    await listItemSell.click();
    await page.getByLabel('Quantity').fill('20'); // Invalid quantity
    await page.getByLabel('Price per Unit').fill('180.00');
    await page.getByLabel('Date').fill('2023-01-20'); // A date after the buy

    // 4. Verify the client-side validation message is shown
    await expect(page.getByText('You do not have enough shares to sell.')).toBeVisible();
    // 5. Verify that the save button is disabled due to client-side validation
    const saveButton = page.getByRole('button', { name: 'Save Transaction' });
    await expect(saveButton).toBeDisabled();


    // 6. Verify the modal is still open and the invalid transaction was not added
    await expect(page.getByRole('heading', { name: 'Add Transaction' })).toBeVisible();
    await page.getByRole('button', { name: 'Cancel' }).click();
    // Verify the holding is unchanged
    await expect(aaplRow.getByRole('cell', { name: '10', exact: true })).toBeVisible();
  });

  test('should display correct data on the dashboard after transactions', async ({ page }) => {
    const portfolioName = `Dashboard Test Portfolio ${faker.string.uuid()}`;

    // 1. Create a portfolio
    const portfolio = await createPortfolio(page.request, portfolioName, 'USD');
    await page.goto(`/portfolio/${portfolio.id}`);

    // 2. Add two different assets
    // Asset 1: 10 GOOGL @ $150
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset').pressSequentially('GOOGL', { delay: 100 }); // Asset already exists from a previous test
    // Wait for the lookup and select the existing asset from the list
    await page.waitForResponse(response => response.url().includes('/api/v1/assets/lookup'));
    const listItem = page.locator(`li:has-text("GOOGL")`);
    await listItem.click();
    await page.getByLabel('Quantity').fill('10');
    await page.getByLabel('Price per Unit').fill('150');
    await page.getByLabel('Date').fill('2023-02-01');
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    // Verify the new holding appears in the HoldingsTable
    const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
    await expect(holdingsTable).toBeVisible();
    const googlRow = holdingsTable.getByRole('row', { name: /GOOGL/ });
    await expect(googlRow).toBeVisible();
    // Use exact match to avoid ambiguity with other cells that might contain '10' (e.g., P&L of ₹10.53)
    await expect(googlRow.getByRole('cell', { name: '10', exact: true })).toBeVisible(); // Quantity

    // 3. Navigate to Dashboard and verify data
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // Verify Total Value. Use a regex to check for a valid currency format,
    // as the exact value will change based on the live market price.
    const totalValueCard = page.locator('.card', { hasText: 'Total Value' });
    await expect(totalValueCard).toContainText(/₹[0-9,]+\.\d{2}/);
  });
});
