import { test, expect, Page } from '@playwright/test';

// Create a unique user for this test file to avoid parallel execution conflicts.
const standardUser = {
  name: 'Corp Actions E2E User',
  email: `ca.e2e.${Date.now()}@example.com`,
  password: 'Password123!',
};

const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe('Corporate Actions E2E Flow', () => {
    const stockTicker = 'MSFT';
    const stockName = 'Microsoft Corporation';

    // Create a standard user for this test suite via the API before any tests run.
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

    // Before each test, log in and set up a portfolio with an initial holding.
    test.beforeEach(async ({ page }) => {
        // 1. Login as the newly created standard user
        await page.goto('/');
        await page.getByLabel('Email address').fill(standardUser.email);
        await page.getByLabel('Password').fill(standardUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

        // 2. Create a new portfolio for this test
        const portfolioName = `Corp Actions Portfolio ${Date.now()}`;
        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByRole('button', { name: 'Create New Portfolio' }).click();

        const createModal = page.locator('.modal-content');
        await expect(createModal).toBeVisible();
        await createModal.getByLabel('Portfolio Name').fill(portfolioName);
        await createModal.getByRole('button', { name: 'Create', exact: true }).click();

        // 3. Verify navigation to the new portfolio's detail page
        await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible({ timeout: 10000 });

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
        await modal.getByLabel('Action Type').selectOption({ label: 'Stock Split' });

        await expect(modal.getByText('Split Ratio')).toBeVisible();
        await modal.getByLabel('Effective Date').fill('2023-02-01');
        await modal.getByLabel('New shares').fill('2');
        await modal.getByLabel('Old shares').fill('1');

        await modal.getByRole('button', { name: 'Save Transaction' }).click();
        await expect(modal).not.toBeVisible();

        await expect(page.getByRole('gridcell', { name: '20' }).first()).toBeVisible({ timeout: 10000 });
        await expect(page.getByRole('gridcell', { name: '₹50.00' })).toBeVisible();

        await page.getByRole('gridcell', { name: stockTicker }).click();
        const detailModal = page.locator('.modal-content');
        await expect(detailModal.getByRole('heading', { name: stockName })).toBeVisible();

        const transactionRow = detailModal.locator('.ag-row', { hasText: 'BUY' });
        await expect(transactionRow.locator('[col-id="quantity"]')).toHaveText('20.0000');
        await expect(transactionRow.locator('[col-id="price_per_unit"]')).toHaveText('₹50.00');
        await expect(transactionRow.locator('[col-id="total_value"]')).toHaveText('₹1,000.00');

        const splitRow = detailModal.locator('.ag-row', { hasText: 'SPLIT' });
        await expect(splitRow).toBeVisible();
        await expect(splitRow.locator('[col-id="quantity"]')).toHaveText('2.0000');
        await expect(splitRow.locator('[col-id="price_per_unit"]')).toHaveText('₹1.00');
    });

    test('should correctly apply a 1-for-1 bonus issue', async ({ page }) => {
        await page.getByRole('button', { name: 'Add Transaction' }).click();

        const modal = page.locator('.modal-content');
        await modal.getByLabel('Asset', { exact: true }).pressSequentially(stockTicker);
        await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/lookup'));
        await modal.locator(`li:has-text("${stockName}")`).click();

        await modal.getByLabel('Transaction Type').selectOption({ label: 'Corporate Action' });
        await modal.getByLabel('Action Type').selectOption({ label: 'Bonus Issue' });

        await expect(modal.getByText('Bonus Ratio')).toBeVisible();
        await modal.getByLabel('Effective Date').fill('2023-03-01');
        await modal.getByLabel('New bonus shares').fill('1');
        await modal.getByLabel('Old held shares').fill('1');

        await modal.getByRole('button', { name: 'Save Transaction' }).click();
        await expect(modal).not.toBeVisible();

        await expect(page.getByRole('gridcell', { name: '20' }).first()).toBeVisible({ timeout: 10000 });
        await expect(page.getByRole('gridcell', { name: '₹50.00' })).toBeVisible();

        await page.getByRole('gridcell', { name: stockTicker }).click();
        const detailModal = page.locator('.modal-content');
        await expect(detailModal.getByRole('heading', { name: stockName })).toBeVisible();

        const bonusTransactionRow = detailModal.locator('.ag-row', { hasText: 'BUY' }).last();
        await expect(bonusTransactionRow.locator('[col-id="quantity"]')).toHaveText('10.0000');
        await expect(bonusTransactionRow.locator('[col-id="price_per_unit"]')).toHaveText('₹0.00');
        await expect(bonusTransactionRow.locator('[col-id="total_value"]')).toHaveText('₹0.00');
    });

    test('should correctly log a reinvested dividend and create a new BUY transaction', async ({ page }) => {
        await page.getByRole('button', { name: 'Add Transaction' }).click();

        const modal = page.locator('.modal-content');
        await modal.getByLabel('Asset', { exact: true }).pressSequentially(stockTicker);
        await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/lookup'));
        await modal.locator(`li:has-text("${stockName}")`).click();

        await modal.getByLabel('Transaction Type').selectOption({ label: 'Corporate Action' });
        await modal.getByLabel('Action Type').selectOption({ label: 'Dividend' });

        await modal.getByLabel('Payment Date').fill('2023-04-01');
        await modal.getByLabel('Total Amount').fill('50');
        await modal.getByLabel('Reinvest this dividend?').check();

        await modal.getByRole('button', { name: 'Save Transaction' }).click();
        await expect(modal).not.toBeVisible();

        await expect(page.getByRole('gridcell', { name: '10.4' }).first()).toBeVisible({ timeout: 10000 });
        await expect(page.getByRole('gridcell', { name: '₹100.96' })).toBeVisible();

        await page.getByRole('gridcell', { name: stockTicker }).click();
        const detailModal = page.locator('.modal-content');
        await expect(detailModal.getByRole('heading', { name: stockName })).toBeVisible();

        const reinvestmentRow = detailModal.locator('.ag-row', { hasText: 'BUY' }).last();
        await expect(reinvestmentRow.locator('[col-id="quantity"]')).toHaveText('0.4000');
        await expect(reinvestmentRow.locator('[col-id="price_per_unit"]')).toHaveText('₹125.00');
        await expect(reinvestmentRow.locator('[col-id="total_value"]')).toHaveText('₹50.00');

        const dividendRow = detailModal.locator('.ag-row', { hasText: 'DIVIDEND' });
        await expect(dividendRow).toBeVisible();
        await expect(dividendRow.locator('[col-id="total_value"]')).toHaveText('₹50.00');
    });
});