import { test, expect } from '@playwright/test';

const testUser = {
  name: 'Txn History User',
  email: 'history@example.com',
  password: 'Secure*123',
};

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
  password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('Transaction History Page', () => {
  let portfolioId: string;
  let asset1Id: string;
  let asset2Id: string;

  // Setup: Create user, portfolio, assets, and transactions via API
  test.beforeAll(async ({ request }) => {

    // 1. Get Admin Token
    const adminLoginResponse = await request.post('/api/v1/auth/login', {
      form: { username: adminUser.email, password: adminUser.password },
    });
    expect(adminLoginResponse.ok()).toBeTruthy();
    const { access_token: adminToken } = await adminLoginResponse.json();
    const adminAuthHeaders = { Authorization: `Bearer ${adminToken}` };

    // 2. Create Standard User
    const userCreateResponse = await request.post('/api/v1/users/', {
      headers: adminAuthHeaders,
      data: { ...testUser, is_admin: false },
    });
    expect(userCreateResponse.ok()).toBeTruthy();

    // 3. Login as Standard User to get their token
    const userLoginResponse = await request.post('/api/v1/auth/login', {
      form: { username: testUser.email, password: testUser.password },
    });
    expect(userLoginResponse.ok()).toBeTruthy();
    const { access_token: userToken } = await userLoginResponse.json();
    const userAuthHeaders = { Authorization: `Bearer ${userToken}` };

    // 4. Create Portfolio
    const portfolioCreateResponse = await request.post('/api/v1/portfolios/', {
      headers: userAuthHeaders,
      data: { name: 'Transaction Test Portfolio', description: 'For E2E tests' },
    });
    expect(portfolioCreateResponse.ok()).toBeTruthy();
    const portfolio = await portfolioCreateResponse.json();
    portfolioId = portfolio.id;

    // 5. Create Assets
    const asset1Response = await request.post('/api/v1/assets/', {
      headers: userAuthHeaders,
      data: { ticker_symbol: 'TXN1', name: 'Transaction Asset 1', asset_type: 'STOCK', currency: 'USD', exchange: 'NASDAQ' },
    });
    expect(asset1Response.ok()).toBeTruthy();
    asset1Id = (await asset1Response.json()).id;

    const asset2Response = await request.post('/api/v1/assets/', {
      headers: userAuthHeaders,
      data: { ticker_symbol: 'TXN2', name: 'Transaction Asset 2', asset_type: 'STOCK', currency: 'USD', exchange: 'NASDAQ' },
    });
    expect(asset2Response.ok()).toBeTruthy();
    asset2Id = (await asset2Response.json()).id;

    // 6. Create Transactions (16 total to test pagination)
    const now = new Date();
    const transactions = [
      // Recent transactions for filtering
      // Older transactions for pagination
      ...Array.from({ length: 13 }, (_, i) => ({
        asset_id: asset1Id,
        transaction_type: 'BUY',
        quantity: 1,
        price_per_unit: 90 - i,
        transaction_date: new Date(now.getTime() - (30 + i) * 24 * 3600 * 1000).toISOString(),
      })),
      { asset_id: asset1Id, transaction_type: 'BUY', quantity: 10, price_per_unit: 100, transaction_date: new Date(now.getTime() - 20 * 24 * 3600 * 1000).toISOString() },
      { asset_id: asset2Id, transaction_type: 'BUY', quantity: 20, price_per_unit: 200, transaction_date: new Date(now.getTime() - 10 * 24 * 3600 * 1000).toISOString() },
      { asset_id: asset1Id, transaction_type: 'SELL', quantity: 5, price_per_unit: 110, transaction_date: new Date(now.getTime() - 5 * 24 * 3600 * 1000).toISOString() },
    ];

    for (const txn of transactions) {
      const txnResponse = await request.post(`/api/v1/portfolios/${portfolioId}/transactions/`, {
        headers: userAuthHeaders,
        data: { ...txn, fees: 1 },
      });
      expect(txnResponse.ok(), `Failed to create transaction: ${await txnResponse.text()}`).toBeTruthy();
    }
  });

  test.beforeEach(async ({ page }) => {
    // Listen for all console events and log them to the test output
    //page.on('console', msg => {
    //  console.log(`[Browser Console] ${msg.type()}: ${msg.text()}`);
    //});

    await page.goto('/');
    await page.getByLabel('Email address').fill(testUser.email);
    await page.getByLabel('Password').fill(testUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should filter transactions and handle pagination', async ({ page }) => {
    //console.log("Clicking Transactions link...");
    await page.getByRole('link', { name: 'Transactions' }).click();
    //console.log("Clicked Transactions link. Current URL:", page.url());
    //await page.screenshot({ path: 'playwright-debug-transactions-page-after-click.png' });
    //console.log("Page content before assertion:\n", await page.content());

    await expect(page.getByRole('heading', { name: 'Transaction History' })).toBeVisible();

    // Initial state: 16 transactions total, 15 visible on page 1
    await expect(page.locator('tbody tr')).toHaveCount(15);
    await expect(page.getByText('Page 1 of 2')).toBeVisible();

    // Filter by Portfolio (should still show 16 total, 15 visible)
    await page.getByLabel('Portfolio').selectOption({ label: 'Transaction Test Portfolio' });
    await expect(page.locator('tbody tr')).toHaveCount(15);

    // Filter by Asset (TXN1 has 13 BUYs + 1 BUY + 1 SELL = 15 transactions)
    await page.getByLabel('Asset').selectOption({ label: 'Transaction Asset 1 (TXN1)' });
    await expect(page.locator('tbody tr')).toHaveCount(15);
    // With exactly 15 results, there is only one page, so pagination controls should not be visible.
    await expect(page.getByText(/Page \d+ of \d+/)).not.toBeVisible();

    // Filter by Type (SELL)
    await page.getByLabel('Type').selectOption({ value: 'SELL' });
    await expect(page.locator('tbody tr')).toHaveCount(1);

    // Scope the search to the table row to avoid ambiguity with the filter dropdown
    const tableRow = page.locator('tbody tr');
    await expect(tableRow.getByText('TXN1')).toBeVisible();
    await expect(tableRow.getByText('SELL')).toBeVisible(); // Check for uppercase 'SELL' in the table
    // Reset filters
    await page.getByRole('button', { name: 'Reset' }).click();
    await expect(page.locator('tbody tr')).toHaveCount(15);

    // Test Pagination
    await page.getByRole('button', { name: 'Next' }).click();
    await expect(page.locator('tbody tr')).toHaveCount(1);
    await expect(page.getByText('Page 2 of 2')).toBeVisible();
  });

  test('should allow editing and deleting a transaction', async ({ page }) => {
    await page.getByRole('link', { name: 'Transactions' }).click();
    await expect(page.getByRole('heading', { name: 'Transaction History' })).toBeVisible();

    // Find the most recent transaction (TXN1 SELL)
    const rowToEdit = page.locator('tbody tr').first();
    const quantityCell = rowToEdit.locator('td').nth(4); // The 5th column is Quantity

    await expect(rowToEdit.getByText('TXN1')).toBeVisible();
    await expect(quantityCell).toHaveText('5'); // Initial quantity is rendered as an integer

    // Edit the transaction
    await rowToEdit.getByRole('button', { name: 'Edit' }).click();
    const modal = page.getByRole('dialog');
    await expect(modal.getByRole('heading', { name: 'Edit Transaction' })).toBeVisible();
    await modal.getByLabel('Quantity').fill('7.5');
    await modal.getByRole('button', { name: 'Save Changes' }).click();

    // Verify the edit
    await expect(modal).not.toBeVisible();
    await expect(quantityCell).toHaveText('7.5'); // Verify the updated quantity

    // Delete the transaction
    await rowToEdit.getByRole('button', { name: 'Delete' }).click();
    const deleteModal = page.getByRole('dialog');
    await expect(deleteModal.getByRole('heading', { name: 'Delete Transaction' })).toBeVisible();

    const deleteResponse = page.waitForResponse(resp => resp.url().includes('/transactions/') && resp.request().method() === 'DELETE' && resp.status() === 200);
    await deleteModal.getByRole('button', { name: 'Confirm Delete' }).click();
    await deleteResponse;

    // Verify the deletion by checking that the modal is gone and the unique content of the row is no longer visible.
    await expect(deleteModal).not.toBeVisible();
    await expect(page.getByRole('cell', { name: '7.5', exact: true })).not.toBeVisible();

    // Verify the total count has been updated and pagination has adjusted.
    await expect(page.locator('tbody tr')).toHaveCount(15);
    await expect(page.getByText(/Page \d+ of \d+/)).not.toBeVisible();
  });
});