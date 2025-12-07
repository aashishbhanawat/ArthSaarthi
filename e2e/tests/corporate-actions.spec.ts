import { test, expect, Page } from '@playwright/test';


const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('Corporate Actions E2E Flow', () => {
    const stockTicker = 'MSFT';
    const stockName = 'Microsoft Corporation';
    let standardUser;

    // Before each test, create a unique user, log in, and set up a portfolio with an initial holding.
    // This ensures each test runs in complete isolation.
    test.beforeEach(async ({ page, request }) => {
        // 1. Create a unique user for this specific test run
        standardUser = {
            name: 'Corp Actions E2E User',
            email: `ca.e2e.${Date.now()}@example.com`,
            password: 'Password123!',
        };

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

        // 2. Login as the newly created standard user
        await page.goto('/');
        await page.getByLabel('Email address').fill(standardUser.email);
        await page.getByLabel('Password').fill(standardUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

        // 2. Create a new portfolio for this test
        const portfolioName = `CA Portfolio ${standardUser.email}`;
        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByRole('button', { name: 'Create New Portfolio' }).click();

        const createModal = page.locator('.modal-content');
        await expect(createModal).toBeVisible();
        await createModal.getByLabel('Portfolio Name').fill(portfolioName);
        await createModal.getByRole('button', { name: 'Create', exact: true }).click();

        // 3. Verify navigation to the new portfolio's detail page and take a screenshot
        await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible({ timeout: 15000 });
        // 4. Create an initial BUY transaction to have holdings to act upon
        await page.getByRole('button', { name: 'Add Transaction' }).click();
        const transactionModal = page.locator('.modal-content');
        await expect(transactionModal).toBeVisible();

        await transactionModal.getByLabel('Asset Type').selectOption('Stock');
        await transactionModal.getByLabel('Transaction Type').selectOption('BUY');
        await transactionModal.getByRole('textbox', { name: 'Asset' }).pressSequentially(stockTicker);

        const listItem = transactionModal.locator(`li:has-text("${stockName}")`);
        await expect(listItem).toBeVisible();
        await listItem.click();

        await transactionModal.getByLabel('Quantity').fill('10');
        await transactionModal.getByLabel('Price per Unit').fill('100');
        await transactionModal.getByLabel('Date').fill('2023-01-15');
        // Wait for potential FX rate fetching (if asset is foreign) to enable the button
        await expect(transactionModal.getByRole('button', { name: 'Save Transaction' })).toBeEnabled();
        await transactionModal.getByRole('button', { name: 'Save Transaction' }).click();
        await expect(transactionModal).not.toBeVisible();

        // 5. Verify the initial holding is present before running the test
        const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
        const holdingRow = holdingsTable.getByRole('row', { name: new RegExp(stockTicker) });
        await expect(holdingRow).toBeVisible({ timeout: 15000 });
        await expect(holdingRow.getByRole('cell', { name: '10', exact: true })).toBeVisible();
        await expect(holdingRow.getByRole('cell', { name: '₹100.00' })).toBeVisible();
    });

    test('should correctly apply a 2-for-1 stock split', async ({ page }) => {
        await page.getByRole('button', { name: 'Add Transaction' }).click();

        const modal = page.locator('.modal-content');
        await expect(modal).toBeVisible();

        await modal.getByLabel('Asset', { exact: true }).pressSequentially(stockTicker);
        await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/lookup'));
        await modal.locator(`li:has-text("${stockName}")`).click();

        await modal.getByLabel('Transaction Type').selectOption({ label: 'Corporate Action' });
        await modal.getByLabel('Action Type', { exact: true }).selectOption({ label: 'Stock Split' });

        await expect(modal.getByText('Split Ratio')).toBeVisible();
        await modal.getByLabel('Effective Date').fill('2023-02-01');
        await modal.getByLabel('New shares').fill('2');
        await modal.getByLabel('Old shares').fill('1');

        await modal.getByRole('button', { name: 'Save Transaction' }).click();
        await expect(modal).not.toBeVisible();

        // Re-locate the table and row to ensure we are not working with a stale reference
        const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
        const updatedHoldingRow = holdingsTable.getByRole('row', { name: new RegExp(stockTicker) });

        await expect(updatedHoldingRow.getByRole('cell', { name: '20' }).first()).toBeVisible({ timeout: 10000 });
        await expect(updatedHoldingRow.getByRole('cell', { name: '₹50.00' })).toBeVisible();

        await updatedHoldingRow.click();
        const detailModal = page.locator('.modal-content');
        await expect(detailModal.getByRole('heading', { name: stockName })).toBeVisible();

        // Wait for the data to load inside the modal by waiting for the loading text to disappear.
        await expect(detailModal.getByText('Loading transactions...')).not.toBeVisible({ timeout: 10000 });

    });

    test('should correctly apply a 1-for-1 bonus issue', async ({ page }) => {
        await page.getByRole('button', { name: 'Add Transaction' }).click();

        const modal = page.locator('.modal-content');
        await modal.getByLabel('Asset', { exact: true }).pressSequentially(stockTicker);
        await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/lookup'));
        await modal.locator(`li:has-text("${stockName}")`).click();

        await modal.getByLabel('Transaction Type').selectOption({ label: 'Corporate Action' });
        await modal.getByLabel('Action Type', { exact: true }).selectOption({ label: 'Bonus Issue' });

        await expect(modal.getByText('Bonus Ratio')).toBeVisible();
        await modal.getByLabel('Effective Date').fill('2023-03-01');
        await modal.getByLabel('New bonus shares').fill('1');
        await modal.getByLabel('Old held shares').fill('1');

        await modal.getByRole('button', { name: 'Save Transaction' }).click();
        await expect(modal).not.toBeVisible();

        const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
        const updatedHoldingRow = holdingsTable.getByRole('row', { name: new RegExp(stockTicker) });

        // Assertions must be sequential to avoid race conditions.
        // 1. First, wait for the quantity to update. This is a reliable first check.
        await expect(updatedHoldingRow.getByRole('cell', { name: '20' }).first()).toBeVisible({ timeout: 15000 });
        // 2. Then, wait for the average price to update. This might take slightly longer.
        await expect(updatedHoldingRow.getByRole('cell', { name: '₹50.00' })).toBeVisible({ timeout: 15000 });

        await updatedHoldingRow.click();
        const detailModal = page.locator('.modal-content');

        // Wait for the data to load inside the modal
        await expect(detailModal.getByText('Loading transactions...')).not.toBeVisible({ timeout: 10000 });

        // The detail modal should show the new zero-cost BUY transaction that
        // resulted from the bonus issue. The BONUS transaction itself is an
        // Use a more robust locator that targets the row by its unique date,
        // as filtering by '₹0.00' can be ambiguous. The date format in the grid might have an optional leading zero.
        const bonusBuyTransactionRow = detailModal.locator('tr', { hasText: /0?1 Mar 2023/ });

        // The modal uses a simple table, so we locate cells by their position (nth).
        // Date=0, Type=1, Quantity=2, Price/Unit=3
        await expect(bonusBuyTransactionRow.locator('td').nth(2)).toHaveText('10');
        await expect(bonusBuyTransactionRow.locator('td').nth(3)).toHaveText('₹0.00');
    });

    test('should correctly log a cash dividend', async ({ page }) => {
        await page.getByRole('button', { name: 'Add Transaction' }).click();

        const modal = page.locator('.modal-content');
        await modal.getByLabel('Asset', { exact: true }).pressSequentially(stockTicker);
        await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/lookup'));
        await modal.locator(`li:has-text("${stockName}")`).click();

        await modal.getByLabel('Transaction Type').selectOption({ label: 'Corporate Action' });
        await modal.getByLabel('Action Type', { exact: true }).selectOption({ label: 'Dividend' });

        await modal.getByLabel('Payment Date').fill('2023-04-01');
        await modal.getByLabel('Total Amount').fill('50');

        await modal.getByRole('button', { name: 'Save Transaction' }).click();
        await expect(modal).not.toBeVisible();

        // 1. Verify the holding quantity has NOT changed on the portfolio page.
        const holdingRow = page.locator('.card', { hasText: 'Holdings' }).getByRole('row', { name: new RegExp(stockTicker) });
        await expect(holdingRow.locator('td').nth(1)).toHaveText('10');

        // 2. Navigate to the global transaction history and verify the dividend was logged.
        await page.getByRole('link', { name: 'Transactions' }).click();
        await expect(page.getByRole('heading', { name: 'Transaction History' })).toBeVisible();

        // Find the new dividend transaction row by its date and asset.
        const dividendRow = page.locator('tr', { hasText: /0?1 Apr 2023/ }).filter({ hasText: stockTicker });
        await expect(dividendRow).toBeVisible();
        await expect(dividendRow).toContainText('DIVIDEND');
        await expect(dividendRow).toContainText('₹50.00');
    });
});