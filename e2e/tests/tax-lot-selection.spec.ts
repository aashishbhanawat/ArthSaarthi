import { test, expect } from '@playwright/test';

const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('Tax Lot Selection E2E Flow', () => {
    // Use pre-seeded asset from global.setup.ts
    const stockTicker = 'AAPL';
    const stockName = 'Apple Inc.';
    let standardUser: any;

    test.beforeEach(async ({ page, request }) => {
        // Mock FX rate for USD assets
        await page.route('**/api/v1/fx-rate/**', route => {
            route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ rate: 85.0 }) });
        });

        standardUser = {
            name: 'Tax Lot User',
            email: `lot.user.${Date.now()}@example.com`,
            password: 'Password123!',
        };

        // Create user via Admin API
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

        // Login
        await page.goto('/');
        await page.getByLabel('Email address').fill(standardUser.email);
        await page.getByLabel('Password').fill(standardUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

        // Create Portfolio
        const portfolioName = `Tax Lot Portfolio`;
        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByRole('button', { name: 'Create New Portfolio' }).click();
        await page.locator('.modal-content').getByLabel('Portfolio Name').fill(portfolioName);
        await page.locator('.modal-content').getByRole('button', { name: 'Create' }).click();
        await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible({ timeout: 15000 });
    });

    test('should allow selling specific tax lots', async ({ page }) => {
        // 1. Buy Lot 1: 10 units @ 100
        await page.getByRole('button', { name: 'Add Transaction' }).click();
        let modal = page.locator('.modal-content');
        await expect(modal).toBeVisible();
        await modal.getByLabel('Asset Type').selectOption('Stock');
        await modal.getByLabel('Transaction Type').selectOption('BUY');

        // Type ticker and select from dropdown (asset is pre-seeded)
        await modal.getByRole('textbox', { name: 'Asset' }).pressSequentially(stockTicker);
        await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/search-stocks'));
        await modal.locator(`li:has-text("${stockName}")`).click();

        await modal.getByLabel('Quantity').fill('10');
        await modal.getByLabel('Price per Unit').fill('100');
        await modal.getByLabel('Date').fill('2023-01-01');
        await expect(modal.getByRole('button', { name: 'Save Transaction' })).toBeEnabled({ timeout: 10000 });
        await modal.getByRole('button', { name: 'Save Transaction' }).click();
        await expect(modal).not.toBeVisible();

        // 2. Buy Lot 2: 10 units @ 200 (Later date)
        await page.getByRole('button', { name: 'Add Transaction' }).click();
        modal = page.locator('.modal-content');
        await expect(modal).toBeVisible();
        await modal.getByLabel('Transaction Type').selectOption('BUY');
        await modal.getByRole('textbox', { name: 'Asset' }).pressSequentially(stockTicker);
        await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/search-stocks'));
        await modal.locator(`li:has-text("${stockName}")`).click();
        await modal.getByLabel('Quantity').fill('10');
        await modal.getByLabel('Price per Unit').fill('200');
        await modal.getByLabel('Date').fill('2023-01-05');
        await expect(modal.getByRole('button', { name: 'Save Transaction' })).toBeEnabled({ timeout: 10000 });
        await modal.getByRole('button', { name: 'Save Transaction' }).click();
        await expect(modal).not.toBeVisible();

        // 3. Sell 5 units - Use "Highest Cost" helper to select Lot 2
        await page.getByRole('button', { name: 'Add Transaction' }).click();
        modal = page.locator('.modal-content');
        await expect(modal).toBeVisible();
        await modal.getByRole('textbox', { name: 'Asset' }).pressSequentially(stockTicker);
        await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/search-stocks'));
        await modal.locator(`li:has-text("${stockName}")`).click();
        await modal.getByLabel('Transaction Type').selectOption('SELL');

        // Verify "Select Tax Lots" section appears
        await expect(modal.getByText('Select Tax Lots (Optional)')).toBeVisible({ timeout: 10000 });
        await expect(modal.getByRole('button', { name: 'FIFO' })).toBeVisible();

        // Wait for lots to load
        await expect(modal.getByText('Loading available lots...')).not.toBeVisible({ timeout: 10000 });

        // Should have 2 lot rows
        const rows = modal.locator('table tbody tr');
        await expect(rows).toHaveCount(2);

        // Fill Quantity first (helpers use this value)
        await modal.getByLabel('Quantity').fill('5');
        await modal.getByLabel('Date').fill('2023-01-10');
        await modal.getByLabel('Price per Unit').fill('250');

        // Click "Highest Cost" - should select from highest priced lot (200)
        await modal.getByRole('button', { name: 'Highest Cost' }).click();

        // Verify Row 2 (highest cost @200) has 5 units selected
        await expect(rows.nth(1).locator('input[type="number"]')).toHaveValue('5');
        // Verify Row 1 (lower cost @100) has 0 units
        const row1Val = await rows.nth(0).locator('input[type="number"]').inputValue();
        expect(Number(row1Val)).toBe(0);

        // Submit
        await expect(modal.getByRole('button', { name: 'Save Transaction' })).toBeEnabled({ timeout: 10000 });
        await modal.getByRole('button', { name: 'Save Transaction' }).click();
        await expect(modal).not.toBeVisible();

        // 4. Verify Result - Check holdings
        // After selling 5 units: Lot 1 has 10, Lot 2 has 5 remaining
        const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
        const holdingRow = holdingsTable.getByRole('row', { name: new RegExp(stockTicker) });
        await expect(holdingRow).toBeVisible({ timeout: 20000 });
        // Total quantity should be 15 (10 from Lot 1 + 5 remaining from Lot 2)
        await expect(holdingRow.getByRole('cell', { name: '15', exact: true })).toBeVisible();
    });
});
