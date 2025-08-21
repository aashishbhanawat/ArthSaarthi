import { test, expect, Page } from '@playwright/test';
import { faker } from '@faker-js/faker';

test.describe.configure({ mode: 'parallel' });

const testUser = {
  name: 'Mapping Test User',
  email: faker.internet.email(),
  password: 'Password123!',
};

const adminUser = {
  email: process.env.VITE_TEST_ADMIN_EMAIL || 'admin@example.com',
  password: process.env.VITE_TEST_ADMIN_PASSWORD || 'AdminPass123!',
};

test.describe('Data Import with Asset Mapping', () => {
  let page: Page;
  const portfolioName = `My Mapping Portfolio ${faker.string.uuid()}`;
  let portfolioId: string;

  test.beforeAll(async ({ browser }) => {
    const apiContext = await browser.newContext();
    const api = apiContext.request;
    // Create the standard user needed for this test file
    const standardUserCreateResponse = await api.post('/api/v1/users/', {
      data: { ...testUser, is_admin: false },
    });
    expect(standardUserCreateResponse.ok()).toBeTruthy();

    const adminLoginResponse = await api.post('/api/v1/auth/token', {
      form: { username: adminUser.email, password: adminUser.password },
    });
    expect(adminLoginResponse.ok()).toBeTruthy();
    const { access_token } = await adminLoginResponse.json();
    const adminAuthHeaders = { Authorization: `Bearer ${access_token}` };

    // Create the target asset 'RELIANCE'
    await api.post('/api/v1/assets/', {
        headers: adminAuthHeaders,
        data: { ticker_symbol: 'RELIANCE', name: 'Reliance Industries', asset_type: 'Stock', currency: 'INR', exchange: 'NSE' },
    });
    await apiContext.dispose();
  });

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    // Login as the standard user before each test.
    await page.goto('/');
    await page.getByLabel('Email address').fill(testUser.email);
    await page.getByLabel('Password').fill(testUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await page.waitForURL('**/dashboard', { timeout: 30000 });
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('should allow a user to map an unrecognized symbol and commit the transaction', async () => {
    // 1. Setup: Create a portfolio
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Portfolio Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByText(portfolioName)).toBeVisible();

    // Get the portfolio ID from the URL
    const url = page.url();
    portfolioId = url.split('/').pop()!;
    expect(portfolioId).toBeDefined();

    // 2. Upload a file with an unrecognized symbol 'RIL'
    await page.getByRole('link', { name: 'Import' }).click();
    await expect(page.getByRole('heading', { name: 'Import Transactions' })).toBeVisible();

    // Select the portfolio and statement type to enable the upload button
    await page.getByLabel('Select Portfolio').selectOption({ label: portfolioName });
    await page.getByLabel('Statement Type').selectOption({ value: 'Generic CSV' });

    const csvContent = 'ticker_symbol,transaction_type,quantity,price_per_unit,transaction_date,fees\nRIL,BUY,10,2800,2023-10-10,15.0';
    await page.getByLabel('Upload a file').setInputFiles({
        name: 'unmapped.csv',
        mimeType: 'text/csv',
        buffer: Buffer.from(csvContent),
    });

    await page.getByRole('button', { name: 'Upload and Preview' }).click();
    // 3. Verify it needs mapping
    await expect(page.getByRole('heading', { name: 'Transactions Needing Mapping (1)' })).toBeVisible();
    const mappingRow = page.locator('tr', { hasText: 'RIL' });
    await expect(mappingRow).toBeVisible();

    // 4. Map the symbol
    await mappingRow.getByRole('button', { name: 'Map Symbol' }).click();
    await expect(page.getByRole('heading', { name: 'Map Unrecognized Symbol' })).toBeVisible();

    await page.getByPlaceholder('Type to search by name or ticker...').fill('RELIANCE');

    // Explicitly wait for the network call to finish before checking the UI
    await page.waitForResponse(response => response.url().includes('/api/v1/assets/lookup'));

    const searchResult = page.locator('li', { hasText: 'RELIANCE' });
    await expect(searchResult).toBeVisible();
    await searchResult.click();
    await page.getByRole('button', { name: 'Create Alias' }).click();

    // 5. Commit and Verify
    await expect(page.getByRole('heading', { name: 'New Transactions (1)' })).toBeVisible();
    const newTransactionRow = page.locator('tr', { hasText: 'RIL' });
    await expect(newTransactionRow).toBeVisible();

    await page.getByRole('button', { name: /Commit \d+ Transactions/ }).click();
    await expect(page.getByText('Successfully committed 1 transactions.')).toBeVisible();

    // Navigate to portfolio and verify transaction
    await page.waitForURL(`**/portfolios/${portfolioId}`);

    // Verify the new holding appears in the HoldingsTable with specific locators
    const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
    const relianceRow = holdingsTable.getByRole('row', { name: /RELIANCE/ });

    await expect(relianceRow).toBeVisible();
    await expect(relianceRow.getByRole('cell', { name: '10', exact: true })).toBeVisible(); // Quantity

    // IMPORTANT: Navigate away to a stable page BEFORE this test finishes.
    // This prevents the PortfolioDetailPage's latent crash from affecting the next test.
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should automatically use the created alias for subsequent imports', async ({ page }) => {
    // 1. Navigate to import page again
    await page.getByRole('link', { name: 'Import' }).click();
    await expect(page.getByRole('heading', { name: 'Import Transactions' })).toBeVisible();

    // Select the portfolio and statement type
    await page.getByLabel('Select Portfolio').selectOption({ label: portfolioName });
    await page.getByLabel('Statement Type').selectOption({ value: 'Generic CSV' });

    // 2. Upload a new file with the same 'RIL' ticker
    const csvContent = 'ticker_symbol,transaction_type,quantity,price_per_unit,transaction_date,fees\nRIL,BUY,5,2900,2023-11-11,10.0';
    await page.getByLabel('Upload a file').setInputFiles({
        name: 'mapped.csv',
        mimeType: 'text/csv',
        buffer: Buffer.from(csvContent),
    });

    await page.getByRole('button', { name: 'Upload and Preview' }).click();

    // 3. Verify it appears directly in "New Transactions"
    // The "Transactions Needing Mapping" heading should not be visible.
    // Instead, we verify the main page heading and the presence of the commit button.
    await expect(page.getByRole('heading', { name: 'Import Preview' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Transactions Needing Mapping' })).not.toBeVisible();
    await expect(page.getByText(/New Transactions \(1\)/)).toBeVisible();
    const newTransactionRow = page.locator('tr', { hasText: 'RIL' });
    await expect(newTransactionRow).toBeVisible();
    await expect(page.getByRole('button', { name: /Commit 1 Transaction/ })).toBeVisible();
  });
});
