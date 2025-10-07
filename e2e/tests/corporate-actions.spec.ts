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

test.describe.serial('Corporate Actions E2E Flow', () => {
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

    test('should correctly apply a 2-for-1 stock split', async ({ page }) => {
        // --- 1. LOGIN ---
        await page.goto('/');
        await page.getByLabel('Email address').fill(standardUser.email);
        await page.getByLabel('Password').fill(standardUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

        // --- 2. CREATE PORTFOLIO ---
        const portfolioName = `Corp Actions Portfolio ${Date.now()}`;
        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByRole('button', { name: 'Create New Portfolio' }).click();
        const createModal = page.locator('.modal-content');
        await expect(createModal).toBeVisible();
        await createModal.getByLabel('Portfolio Name').fill(portfolioName);
        await createModal.getByRole('button', { name: 'Create', exact: true }).click();
        await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible({ timeout: 10000 });

        // --- 3. CREATE INITIAL TRANSACTION ---
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

        // --- 4. VERIFY INITIAL STATE ---
        const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
        const holdingRow = holdingsTable.getByRole('row', { name: new RegExp(stockTicker) });
        await expect(holdingRow).toBeVisible({ timeout: 15000 });
        await expect(holdingRow.getByRole('cell', { name: '10', exact: true })).toBeVisible();
        await expect(holdingRow.getByRole('cell', { name: '₹100.00' })).toBeVisible();

        // --- 5. LOG THE STOCK SPLIT ---
        await page.getByRole('button', { name: 'Add Transaction' }).click();
        const splitModal = page.locator('.modal-content');
        await expect(splitModal).toBeVisible();
        await splitModal.getByLabel('Asset', { exact: true }).pressSequentially(stockTicker);
        await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/lookup'));
        await splitModal.locator(`li:has-text("${stockName}")`).click();
        await splitModal.getByLabel('Transaction Type').selectOption({ label: 'Corporate Action' });
        await splitModal.getByLabel('Action Type', { exact: true }).selectOption({ label: 'Stock Split' });
        await splitModal.getByLabel('Effective Date').fill('2023-02-01');
        await splitModal.getByLabel('New shares').fill('2');
        await splitModal.getByLabel('Old shares').fill('1');
        await splitModal.getByRole('button', { name: 'Save Transaction' }).click();
        await expect(splitModal).not.toBeVisible();

        // --- 6. DIAGNOSTIC WAIT & VERIFICATION ---
        // This is a temporary, bad-practice wait to diagnose a race condition.
        await page.waitForTimeout(1000);

        await expect(page.getByRole('gridcell', { name: '20' }).first()).toBeVisible({ timeout: 10000 });
        await expect(page.getByRole('gridcell', { name: '₹50.00' })).toBeVisible();
    });
});