import { test, expect } from '@playwright/test';

const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('ESPP and RSU Tracking E2E Flow', () => {
    const stockTicker = 'MSFT';
    const stockName = 'Microsoft Corporation';
    let standardUser;
    let portfolioName;

    test.beforeEach(async ({ page, request }) => {
        // 1. Create a unique user for this specific test run
        standardUser = {
            name: 'ESPP RSU User',
            email: `espp.rsu.${Date.now()}@example.com`,
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

        // 3. Create a new portfolio for this test
        portfolioName = `ESPP RSU Portfolio ${Date.now()}`;
        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByRole('button', { name: 'Create New Portfolio' }).click();
        await page.getByLabel('Name').fill(portfolioName);
        await page.getByRole('button', { name: 'Create', exact: true }).click();
        await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();
    });

    test('should allow a user to add an RSU grant with Sell to Cover', async ({ page }) => {
        // 1. Open "Add ESPP/RSU Award" modal
        await page.getByRole('button', { name: 'Additional actions' }).click();
        await page.getByRole('menuitem', { name: 'Add ESPP/RSU Award' }).click();

        const modal = page.locator('.modal-content');
        await expect(modal).toBeVisible();
        await expect(modal.getByRole('heading', { name: 'Add ESPP/RSU Award' })).toBeVisible();

        // 2. Fill out RSU details
        await modal.getByLabel('RSU Vest').check();

        await modal.getByLabel('Asset', { exact: true }).pressSequentially(stockTicker);
        await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/lookup'));
        await page.locator(`div[role="option"]:has-text("${stockName}")`).first().click();

        await modal.getByLabel('Vest Date').fill('2023-11-15');
        await modal.getByLabel('Gross Qty Vested').fill('10');
        await modal.getByLabel('FMV at Vest (USD)').fill('150.25');

        // Handle FX Rate: Wait for auto-fetch or allow manual entry
        const fxRateInput = modal.getByLabel('FX Rate (USD-INR)');
        await expect(async () => {
            const val = await fxRateInput.inputValue();
            const editable = await fxRateInput.isEditable();
            if (val) return; // Fetched successfully
            if (editable) {
                await fxRateInput.fill('83.50');
                return;
            }
            // If neither, we are still loading...
            throw new Error("Waiting for FX Rate...");
        }).toPass({ timeout: 10000 });

        // 3. Fill "Sell to Cover" details
        await modal.getByLabel("Record 'Sell to Cover' for taxes").check();
        await expect(modal.getByLabel('Shares Sold')).toBeVisible();

        await modal.getByLabel('Shares Sold').fill('4');
        await modal.getByLabel('Sale Price (USD)').fill('150.25');

        await modal.getByRole('button', { name: 'Add Award' }).click();
        await expect(modal).not.toBeVisible();

        // 4. Verify Transactions
        // Navigate to Transaction History to see individual entries
        await page.getByRole('link', { name: 'Transactions' }).click();
        await expect(page.getByRole('heading', { name: 'Transaction History' })).toBeVisible();

        const rsuRow = page.locator('tr', { hasText: 'RSU Vest' });
        await expect(rsuRow).toBeVisible();
        await expect(rsuRow).toContainText('10'); // Quantity

        const sellRow = page.locator('tr', { hasText: 'SELL' });
        await expect(sellRow).toBeVisible();
        await expect(sellRow).toContainText('4'); // Quantity

        // 5. Verify Holdings
        // Navigate back to the portfolio detail page from Transactions page
        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByText(portfolioName).click();
        await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

        const holdingsTable = page.locator('.card', { hasText: 'Holdings' });

        await expect(holdingsTable).toBeVisible();

        const holdingRow = holdingsTable.getByRole('row', { name: new RegExp(stockTicker) });
        await expect(holdingRow).toBeVisible();
        // Net quantity should be 10 - 4 = 6
        await expect(holdingRow.getByRole('cell', { name: '6', exact: true })).toBeVisible();
    });

    test('should allow a user to add an ESPP Purchase', async ({ page }) => {
         // 1. Open "Add ESPP/RSU Award" modal
        await page.getByRole('button', { name: 'Additional actions' }).click();
        await page.getByRole('menuitem', { name: 'Add ESPP/RSU Award' }).click();

        const modal = page.locator('.modal-content');
        await expect(modal).toBeVisible();

        // 2. Select ESPP
        await modal.getByLabel('ESPP Purchase').check();

        // 3. Fill ESPP Details
        await modal.getByLabel('Asset', { exact: true }).pressSequentially(stockTicker);
        await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/lookup'));
        await page.locator(`div[role="option"]:has-text("${stockName}")`).first().click();

        await modal.getByLabel('Purchase Date').fill('2023-12-01');
        await modal.getByLabel('Quantity').fill('25');
        await modal.getByLabel('Purchase Price (USD)').fill('340.00');
        await modal.getByLabel('Market Price (USD)').fill('400.00');

        // Handle FX Rate: Wait for auto-fetch or allow manual entry
        const fxRateInput = modal.getByLabel('FX Rate (USD-INR)');
        await expect(async () => {
            const val = await fxRateInput.inputValue();
            const editable = await fxRateInput.isEditable();
            if (val) return; // Fetched successfully
            if (editable) {
                await fxRateInput.fill('83.60');
                return;
            }
            throw new Error("Waiting for FX Rate...");
        }).toPass({ timeout: 10000 });

        await modal.getByRole('button', { name: 'Add Award' }).click();
        await expect(modal).not.toBeVisible();

        // 4. Verify Holdings
        const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
        const holdingRow = holdingsTable.getByRole('row', { name: new RegExp(stockTicker) });
        await expect(holdingRow).toBeVisible();
        await expect(holdingRow.getByRole('cell', { name: '25', exact: true })).toBeVisible();

        // Verify Transaction Type in History
         await page.getByRole('link', { name: 'Transactions' }).click();
        const esppRow = page.locator('tr', { hasText: 'ESPP Purchase' });
        await expect(esppRow).toBeVisible();
        await expect(esppRow).toContainText('25');
    });
});
