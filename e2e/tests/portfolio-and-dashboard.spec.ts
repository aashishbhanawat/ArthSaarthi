import { test, expect, Page } from '@playwright/test';

const standardUser = {
  name: 'Standard User E2E',
  email: `standard.e2e.${Date.now()}@example.com`,
  password: 'Password123!',
};

const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('Portfolio and Dashboard E2E Flow', () => {
  test.beforeAll(async ({ request }) => {
    // The global setup has already created the admin user.
    // We just need to log in as admin to create our test-specific standard user.
    const adminLoginResponse = await request.post('/api/v1/auth/login', {
      form: { username: adminUser.email, password: adminUser.password },
    });
    expect(adminLoginResponse.ok()).toBeTruthy();
    const { access_token } = await adminLoginResponse.json();
    const adminAuthHeaders = { Authorization: `Bearer ${access_token}` };

    // Create Standard User via API (as Admin)
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

  test('should allow a user to create, view, and delete a portfolio', async ({ page }) => {
    const portfolioName = `My E2E Portfolio ${Date.now()}`;

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
    await portfolioRow.getByRole('button', { name: `Delete portfolio ${portfolioName}` }).click();

    await expect(page.getByRole('dialog')).toBeVisible(); // Verify the modal is open
    // Scope the search to the dialog to click the correct "Delete" button
    await page.getByRole('dialog').getByRole('button', { name: 'Delete' }).click();

    // Verify deletion
    await expect(page.getByRole('heading', { name: 'Portfolios' })).toBeVisible();
    await expect(portfolioRow).not.toBeVisible();
  });

  test('should display holdings in a collapsible section with correct data', async ({ page }) => {
    const portfolioName = `My Holdings Portfolio ${Date.now()}`;
    const stockName = 'MSFT';
    const mfName = 'Mirae Asset Large Cap Fund';

    // 1. Create a portfolio
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // 2. Add a Stock transaction
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset Type').selectOption('Stock');
    await page.getByLabel('Type', { exact: true }).selectOption('BUY');
    await page.getByRole('textbox', { name: 'Asset' }).pressSequentially(stockName);
    await page.locator(`li:has-text("${stockName}")`).click();
    await page.getByLabel('Quantity').fill('50');
    await page.getByLabel('Price per Unit').fill('300.00');
    await page.getByLabel('Date').fill('2023-03-01');
    await page.getByRole('button', { name: 'Save Transaction' }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible(); // Wait for navigation

    // 3. Add a Mutual Fund transaction
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset Type').selectOption('Mutual Fund');
    await page.getByLabel('Type', { exact: true }).selectOption('BUY');
    await page.getByRole('combobox', { name: 'Asset', exact: true }).fill('Mirae');
    await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/search-mf'));
    await page.getByText(mfName).click();
    await page.getByLabel('Quantity').fill('100');
    await page.getByLabel('Price per Unit').fill('45.50');
    await page.getByLabel('Date').fill('2023-03-05');
    await page.getByRole('button', { name: 'Save Transaction' }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible(); // Wait for navigation

    // 4. Verify the new UI
    const equitiesSection = page.locator('div:has-text("Equities & Mutual Funds") >> ..').first();
    await expect(equitiesSection.getByRole('row', { name: new RegExp(mfName) })).toBeVisible();
    await expect(equitiesSection.getByRole('button', { name: /Equities & Mutual Funds/ })).toBeVisible();

    // Check that the section is expanded by default and contains the correct headers
    const equitiesContent = equitiesSection.locator('table');
    await expect(equitiesContent).toBeVisible();
    await expect(equitiesContent.getByRole('columnheader', { name: 'Asset' })).toBeVisible();
    await expect(equitiesContent.getByRole('columnheader', { name: 'Qty' })).toBeVisible();
    await expect(equitiesContent.getByRole('columnheader', { name: 'Avg. Price' })).toBeVisible();
    await expect(equitiesContent.getByRole('columnheader', { name: 'LTP' })).toBeVisible();
    await expect(equitiesContent.getByRole('columnheader', { name: 'Value' })).toBeVisible();

    // Check that both assets are in the table
    await expect(equitiesContent.getByRole('row', { name: new RegExp(stockName) })).toBeVisible();
    await expect(equitiesContent.getByRole('row', { name: new RegExp(mfName) })).toBeVisible();

    // 5. Test collapse and expand
    const equitiesTrigger = equitiesSection.getByRole('button', { name: /Equities & Mutual Funds/ });
    await equitiesTrigger.click();
    await expect(equitiesContent).not.toBeVisible();
    await equitiesTrigger.click();
    await expect(equitiesContent).toBeVisible();
  });

  test('should prevent a user from creating an invalid SELL transaction', async ({ page }) => {
    const portfolioName = `Invalid Sell Portfolio ${Date.now()}`;
    const assetName = 'AAPL'; // Use a different asset to avoid test contamination

    // 1. Create a portfolio
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // 2. Add a BUY transaction for 10 shares
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset Type').selectOption('Stock');
    await page.getByLabel('Type', { exact: true }).selectOption('BUY');
    await page.getByRole('textbox', { name: 'Asset' }).pressSequentially(assetName);
    const listItem = page.locator(`li:has-text("${assetName}")`);
    await expect(listItem).toBeVisible();
    await listItem.click();
    await page.getByLabel('Quantity').fill('10');
    await page.getByLabel('Price per Unit').fill('175.00');
    await page.getByLabel('Date').fill('2023-01-15'); // Use a fixed past date
    await page.getByRole('button', { name: 'Save Transaction' }).click();
    // Verify the new holding appears in the HoldingsTable
    const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
    await expect(holdingsTable).toBeVisible();
    const aaplRow = holdingsTable.getByRole('row', { name: /AAPL/ });
    await expect(aaplRow).toBeVisible();
    await expect(aaplRow.getByRole('cell', { name: '10', exact: true })).toBeVisible(); // Quantity

    // 3. Attempt to SELL 20 shares (which is more than owned)
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset Type').selectOption('Stock');
    await page.getByLabel('Type', { exact: true }).selectOption('SELL');
    await page.getByRole('textbox', { name: 'Asset' }).pressSequentially(assetName);
    await page.waitForResponse(response => response.url().includes('/api/v1/assets/lookup'));
    const listItemSell = page.locator(`li:has-text("${assetName}")`);
    await expect(listItemSell).toBeVisible();
    await listItemSell.click();
    await page.getByLabel('Quantity').fill('20'); // Invalid quantity
    await page.getByLabel('Price per Unit').fill('180.00');
    await page.getByLabel('Date').fill('2023-01-20'); // A date after the buy
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    // 4. Verify the backend error is displayed in the modal
    await expect(page.locator('.alert-error')).toBeVisible();
    await expect(page.locator('.alert-error')).toContainText('Insufficient holdings to sell');

    // 5. Verify the modal is still open and the invalid transaction was not added
    await expect(page.getByRole('heading', { name: 'Add Transaction' })).toBeVisible();
    await page.getByRole('button', { name: 'Cancel' }).click();
    // Verify the holding is unchanged
    await expect(aaplRow.getByRole('cell', { name: '10', exact: true })).toBeVisible();
  });

  test('should display correct data on the dashboard after transactions', async ({ page }) => {
    const portfolioName = `Dashboard Test Portfolio ${Date.now()}`;

    // 1. Create a portfolio
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // 2. Add two different assets
    // Asset 1: 10 GOOGL @ $150
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset Type').selectOption('Stock');
    await page.getByLabel('Type', { exact: true }).selectOption('BUY');
    await page.getByRole('textbox', { name: 'Asset' }).pressSequentially('GOOGL'); // Asset already exists from a previous test
    const listItem = page.locator(`li:has-text("GOOGL")`);
    await expect(listItem).toBeVisible();
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
    // Use exact match to avoid ambiguity with other cells that might contain '10' (e.g., P&L of ₹10.44)
    await expect(googlRow.getByRole('cell', { name: '10', exact: true })).toBeVisible(); // Quantity

    // 3. Navigate to Dashboard and verify data
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // Verify Total Value. Use a regex to check for a valid currency format,
    // as the exact value will change based on the live market price.
    const totalValueCard = page.locator('.card', { hasText: 'Total Value' });
    await expect(totalValueCard).toContainText(/₹[0-9,]+\.\d{2}/);
  });

  test('should allow adding a mutual fund transaction', async ({ page }) => {
    const portfolioName = `My MF Portfolio ${Date.now()}`;
    const mfSearchTerm = 'Axis';
    const mfFullName = 'Axis Bluechip Fund - Direct Plan - Growth';

    // 1. Create a portfolio to hold transactions
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // 2. Add a BUY transaction for a Mutual Fund
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset Type').selectOption('Mutual Fund');
    await page.getByLabel('Type', { exact: true }).selectOption('BUY');

    // Search for the MF
    // Use a more specific locator to distinguish from the "Asset Type" dropdown.
    // The react-select component for MF search has a role of 'combobox'.
    await page.getByRole('combobox', { name: 'Asset', exact: true }).fill(mfSearchTerm);
    await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/search-mf'));

    // Select the MF from the results
    await page.getByText(mfFullName, { exact: true }).click();

    // Fill the rest of the form
    await page.getByLabel('Quantity').fill('50');
    await page.getByLabel('Price per Unit').fill('58.98'); // NAV
    await page.getByLabel('Date').fill(new Date().toISOString().split('T')[0]);
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    // 3. Verify the new holding appears in the HoldingsTable
    const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
    await expect(holdingsTable).toBeVisible();
    const mfRow = holdingsTable.getByRole('row', { name: new RegExp(mfFullName) });
    await expect(mfRow).toBeVisible();
    await expect(mfRow.getByRole('cell', { name: '50', exact: true })).toBeVisible(); // Quantity
  });
});
