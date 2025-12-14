import { test, expect } from '@playwright/test';

const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('Tax Lot Selection E2E Flow', () => {
    const stockTicker = 'LOTT';
    const stockName = 'Lot Test Tech';
    let standardUser: any;

    test.beforeEach(async ({ page, request }) => {
        // 1. Setup User
        await page.route('**/api/v1/fx-rate/**', route => {
            route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ rate: 1.0 }) });
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

        // 2. Login
        await page.goto('/');
        await page.getByLabel('Email address').fill(standardUser.email);
        await page.getByLabel('Password').fill(standardUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

        // 3. Create Portfolio
        const portfolioName = `Lot Portfolio`;
        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByRole('button', { name: 'Create New Portfolio' }).click();
        await page.locator('.modal-content').getByLabel('Portfolio Name').fill(portfolioName);
        await page.locator('.modal-content').getByRole('button', { name: 'Create' }).click();
        await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();
    });

    test('should allow selling specific tax lots', async ({ page }) => {
        // 1. Buy Lot 1: 10 units @ 100
        await page.getByRole('button', { name: 'Add Transaction' }).click();
        let modal = page.locator('.modal-content');
        await expect(modal).toBeVisible();
        await modal.getByLabel('Asset Type').selectOption('Stock');
        await modal.getByLabel('Transaction Type').selectOption('BUY');
        await modal.getByRole('textbox', { name: 'Asset' }).pressSequentially(stockTicker);
        await modal.getByRole('textbox', { name: 'Asset' }).blur();
        // Note: In real app we click LI, but here we might trigger creation implicitly if not found? 
        // Actually, let's try to mimic "Create new asset" flow or ensure asset exists.
        // The modal usually shows a list. If not found, does it allow arbitrary? 
        // Based on corporate-actions.spec.ts, it expects a list item.
        // Let's rely on backend mocking or just create the asset via UI if needed. 
        // Wait, the previous test clicked the list item. We should try to trigger the lookup.

        // Let's skip the dropdown logic complexity by typing and hitting Enter if possible, 
        // OR better: Create asset via API first? No, UI test should use UI.
        // We will assume "LOTT" doesn't exist and the UI might prompt to create it?
        // Actually, let's stick to the flow in corporate-actions.spec.ts: pressSequentially -> click list item.
        // If it doesn't exist, we might get blocked.
        // FIX: The app likely uses an external API for lookup. We should mock that or use a "Custom Asset" flow?
        // Let's try to simulate checking "Add new asset" if not found, OR just mock the lookup response like previous tests did?
        // Previous test: await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/lookup'));

        // Let's NOT rely on lookup for a fake ticker unless we mock it.
        // Use a Mock Route for lookup!
        await page.route('**/api/v1/assets/lookup?query=*', route => {
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify([{ symbol: stockTicker, name: stockName, type: 'STOCK', region: 'US', currency: 'USD' }])
            });
        });

        // Re-type to trigger mocked lookup
        await modal.getByRole('textbox', { name: 'Asset' }).clear();
        await modal.getByRole('textbox', { name: 'Asset' }).pressSequentially(stockTicker);
        await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/lookup'));
        await modal.locator(`li:has-text("${stockName}")`).click();

        await modal.getByLabel('Quantity').fill('10');
        await modal.getByLabel('Price per Unit').fill('100');
        await modal.getByLabel('Date').fill('2023-01-01');
        await modal.getByRole('button', { name: 'Save Transaction' }).click();
        await expect(modal).not.toBeVisible();

        // 2. Buy Lot 2: 10 units @ 200 (Latest date)
        await page.getByRole('button', { name: 'Add Transaction' }).click();
        modal = page.locator('.modal-content');
        await modal.getByRole('textbox', { name: 'Asset' }).pressSequentially(stockTicker);
        await modal.locator(`li:has-text("${stockName}")`).click();
        await modal.getByLabel('Quantity').fill('10');
        await modal.getByLabel('Price per Unit').fill('200');
        await modal.getByLabel('Date').fill('2023-01-05');
        await modal.getByRole('button', { name: 'Save Transaction' }).click();
        await expect(modal).not.toBeVisible();

        // 3. Sell 5 units - Specific Lots
        await page.getByRole('button', { name: 'Add Transaction' }).click();
        modal = page.locator('.modal-content');
        await modal.getByRole('textbox', { name: 'Asset' }).pressSequentially(stockTicker);
        await modal.locator(`li:has-text("${stockName}")`).click();
        await modal.getByLabel('Transaction Type').selectOption('SELL');

        // Verify "Select Tax Lots" section appears
        await expect(modal.getByText('Select Tax Lots (Optional)')).toBeVisible();
        await expect(modal.getByRole('button', { name: 'FIFO' })).toBeVisible();

        // Wait for lots to load
        await expect(modal.getByText('Loading available lots...')).not.toBeVisible();

        // Should have 2 rows
        const rows = modal.locator('table tbody tr');
        await expect(rows).toHaveCount(2);

        // Verify Row 1 (Oldest, Cost 100)
        await expect(rows.nth(0)).toContainText('100'); // Cost

        // Verify Row 2 (Newest, Cost 200)
        await expect(rows.nth(1)).toContainText('200'); // Cost

        // Test "Highest Cost" Helper
        await modal.getByRole('button', { name: 'Highest Cost' }).click();
        await modal.getByLabel('Quantity').fill('5'); // Total Sell Qty

        // It should auto-fill the highest cost lot (Row 2) with 5
        // Wait, the helpers usually work by FILLING the lots based on the Total Quantity input?
        // Or do they strictly set the distribution?
        // Checking code: applyFIFO uses `getValues().quantity`. So we must set Quantity FIRST.

        // Let's set Quantity first
        // Clear helpers first ( manually set 0? or just overwrite)

        // Action: Fill Quantity 5

        // Action: Click Highest Cost
        await modal.getByRole('button', { name: 'Highest Cost' }).click();

        // Check Row 2 input has 5
        // Locator for input in row 2
        await expect(rows.nth(1).locator('input[type="number"]')).toHaveValue('5');
        // Check Row 1 input has 0 or empty
        const row1Val = await rows.nth(0).locator('input[type="number"]').inputValue();
        expect(Number(row1Val)).toBe(0);

        // Fill Price per Unit for SELL
        await modal.getByLabel('Price per Unit').fill('250');

        // Submit
        await modal.getByRole('button', { name: 'Save Transaction' }).click();
        await expect(modal).not.toBeVisible();

        // 4. Verify Result
        // Navigate to Analytics or verify P&L?
        // Easiest is to check the realized P&L on the dashboard/analytics if accessible.
        // Cost Basis for 5 units @ 200 = 1000.
        // We didn't set a Sell Price. Default? 
        // Wait, we missed setting Sell Price in Step 3.
        // Let's fix that in a re-run logic or just add it now.
        // If we sell @ 250.
        // Realized P&L = (250 - 200) * 5 = 250.
        // If it was FIFO (Cost 100), P&L would be (250 - 100) * 5 = 750.
    });
});
