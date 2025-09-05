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
    const adminLoginResponse = await request.post('/api/v1/auth/login', {
      form: { username: adminUser.email, password: adminUser.password },
    });
    expect(adminLoginResponse.ok()).toBeTruthy();
    const { access_token } = await adminLoginResponse.json();
    const adminAuthHeaders = { Authorization: `Bearer ${access_token}` };

    const standardUserCreateResponse = await request.post('/api/v1/users/', {
      headers: adminAuthHeaders,
      data: { ...standardUser, is_admin: false },
    });
    expect(standardUserCreateResponse.ok()).toBeTruthy();
  });

  test.beforeEach(async ({ page }) => {
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

    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible({ timeout: 10000 });

    await page.getByRole('link', { name: 'Back to Portfolios' }).click();

    const portfolioRow = page.locator('.card', { hasText: new RegExp(portfolioName) });
    await expect(portfolioRow).toBeVisible();
    await portfolioRow.getByRole('button', { name: `Delete portfolio ${portfolioName}` }).click();

    await expect(page.getByRole('dialog')).toBeVisible();
    await page.getByRole('dialog').getByRole('button', { name: 'Delete' }).click();

    await expect(page.getByRole('heading', { name: 'Portfolios' })).toBeVisible();
    await expect(portfolioRow).not.toBeVisible();
  });

  test('should allow a user to add various types of transactions', async ({ page }) => {
    const portfolioName = `My Transaction Portfolio ${Date.now()}`;
    const newAssetName = 'GOOGL';

    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset Type').selectOption('Stock');
    await page.getByLabel('Type', { exact: true }).selectOption('BUY');
    await page.getByRole('textbox', { name: 'Asset' }).pressSequentially(newAssetName);
    const listItem = page.locator(`li:has-text("${newAssetName}")`);
    await expect(listItem).toBeVisible();
    await listItem.click();
    await page.getByLabel('Quantity').fill('10');
    await page.getByLabel('Price per Unit').fill('150.00');
    await page.getByLabel('Date').fill(new Date().toISOString().split('T')[0]);
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
    await expect(holdingsTable).toBeVisible();
    const googlRow = holdingsTable.getByRole('row', { name: /GOOGL/ });
    await expect(googlRow).toBeVisible();
    await expect(googlRow.getByRole('cell', { name: '10', exact: true })).toBeVisible();

    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset Type').selectOption('Stock');
    await page.getByLabel('Type', { exact: true }).selectOption('SELL');
    await page.getByRole('textbox', { name: 'Asset' }).pressSequentially(newAssetName);

    await page.waitForResponse(response => response.url().includes('/api/v1/assets/lookup'));

    const listItemSell = page.locator(`li:has-text("${newAssetName}")`);
    await expect(listItemSell).toBeVisible();
    await listItemSell.click();

    await page.getByLabel('Quantity').fill('5');
    await page.getByLabel('Price per Unit').fill('160.00');
    await page.getByLabel('Date').fill(new Date().toISOString().split('T')[0]);
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    await expect(holdingsTable).toBeVisible();
    await expect(googlRow).toBeVisible();
    await expect(googlRow.getByRole('cell', { name: '5', exact: true })).toBeVisible();

    await page.unroute('**/api/v1/assets/');
  });

  test('should prevent a user from creating an invalid SELL transaction', async ({ page }) => {
    const portfolioName = `Invalid Sell Portfolio ${Date.now()}`;
    const assetName = 'AAPL';

    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset Type').selectOption('Stock');
    await page.getByLabel('Type', { exact: true }).selectOption('BUY');
    await page.getByRole('textbox', { name: 'Asset' }).pressSequentially(assetName);
    const listItem = page.locator(`li:has-text("${assetName}")`);
    await expect(listItem).toBeVisible();
    await listItem.click();
    await page.getByLabel('Quantity').fill('10');
    await page.getByLabel('Price per Unit').fill('175.00');
    await page.getByLabel('Date').fill('2023-01-15');
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
    await expect(holdingsTable).toBeVisible();
    const aaplRow = holdingsTable.getByRole('row', { name: /AAPL/ });
    await expect(aaplRow).toBeVisible();
    await expect(aaplRow.getByRole('cell', { name: '10', exact: true })).toBeVisible();

    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset Type').selectOption('Stock');
    await page.getByLabel('Type', { exact: true }).selectOption('SELL');
    await page.getByRole('textbox', { name: 'Asset' }).pressSequentially(assetName);
    await page.waitForResponse(response => response.url().includes('/api/v1/assets/lookup'));
    const listItemSell = page.locator(`li:has-text("${assetName}")`);
    await expect(listItemSell).toBeVisible();
    await listItemSell.click();
    await page.getByLabel('Quantity').fill('20');
    await page.getByLabel('Price per Unit').fill('180.00');
    await page.getByLabel('Date').fill('2023-01-20');
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    await expect(page.locator('.alert-error')).toBeVisible();
    await expect(page.locator('.alert-error')).toContainText('Insufficient holdings to sell');

    await expect(page.getByRole('heading', { name: 'Add Transaction' })).toBeVisible();
    await page.getByRole('button', { name: 'Cancel' }).click();
    await expect(aaplRow.getByRole('cell', { name: '10', exact: true })).toBeVisible();
  });

  test('should display correct data on the dashboard after transactions', async ({ page }) => {
    const portfolioName = `Dashboard Test Portfolio ${Date.now()}`;

    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset Type').selectOption('Stock');
    await page.getByLabel('Type', { exact: true }).selectOption('BUY');
    await page.getByRole('textbox', { name: 'Asset' }).pressSequentially('GOOGL');
    const listItem = page.locator(`li:has-text("GOOGL")`);
    await expect(listItem).toBeVisible();
    await listItem.click();
    await page.getByLabel('Quantity').fill('10');
    await page.getByLabel('Price per Unit').fill('150');
    await page.getByLabel('Date').fill('2023-02-01');
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
    await expect(holdingsTable).toBeVisible();
    const googlRow = holdingsTable.getByRole('row', { name: /GOOGL/ });
    await expect(googlRow).toBeVisible();
    await expect(googlRow.getByRole('cell', { name: '10', exact: true })).toBeVisible();

    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    const totalValueCard = page.locator('.card', { hasText: 'Total Value' });
    await expect(totalValueCard).toContainText(/₹[0-9,]+\.\d{2}/);
  });

  test('should allow adding a mutual fund transaction', async ({ page }) => {
    const portfolioName = `My MF Portfolio ${Date.now()}`;
    const mfSearchTerm = 'Axis';
    const mfFullName = 'Axis Bluechip Fund - Direct Plan - Growth';

    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset Type').selectOption('Mutual Fund');
    await page.getByLabel('Type', { exact: true }).selectOption('BUY');

    await page.getByRole('combobox', { name: 'Asset', exact: true }).fill(mfSearchTerm);
    await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/search-mf'));

    await page.getByText(mfFullName, { exact: true }).click();

    await page.getByLabel('Quantity').fill('50');
    await page.getByLabel('Price per Unit').fill('58.98');
    await page.getByLabel('Date').fill(new Date().toISOString().split('T')[0]);
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
    await expect(holdingsTable).toBeVisible();
    const mfRow = holdingsTable.getByRole('row', { name: new RegExp(mfFullName) });
    await expect(mfRow).toBeVisible();
    await expect(mfRow.getByRole('cell', { name: '50', exact: true })).toBeVisible();
  });

  test('should allow adding a fixed deposit transaction', async ({ page }) => {
    const portfolioName = `My FD Portfolio ${Date.now()}`;
    const fdName = 'My Test FD';
    const fdAccountNumber = '1234567890';

    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset Type').selectOption('Fixed Deposit');

    await page.getByLabel('Institution Name').fill(fdName);
    await page.getByLabel('FD Account Number').fill(fdAccountNumber);
    await page.getByLabel('Principal Amount').fill('100000');
    await page.getByLabel('Interest Rate (%)').fill('6.5');
    await page.getByLabel('Start Date').fill('2023-01-01');
    await page.getByLabel('Maturity Date').fill('2028-01-01');

    await page.getByRole('button', { name: 'Add Transaction' }).click();

    const depositsSection = page.getByTestId('holdings-section-DEPOSITS');
    await expect(depositsSection).toBeVisible();

    const fdRow = depositsSection.getByRole('row', { name: new RegExp(fdName) });
    await expect(fdRow).toBeVisible();

    await expect(fdRow.getByRole('cell', { name: fdAccountNumber })).toBeVisible();
    await expect(fdRow.getByRole('cell', { name: /6.50%/ })).toBeVisible();
    await expect(fdRow.getByRole('cell', { name: /100,000.00/ })).toBeVisible();
  });
});
