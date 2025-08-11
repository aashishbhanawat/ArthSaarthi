import { test, expect } from '@playwright/test';

test.describe.serial('Data Import with Asset Mapping', () => {
    const portfolioName = `My Mapping Portfolio ${Date.now()}`;
    let portfolioId: string;

    test.beforeAll(async ({ request }) => {
        // Reset the database to a clean state
        const response = await request.post('/api/v1/testing/reset-db');
        expect(response.status()).toBe(204);
    });

    test('should allow a user to map an unrecognized symbol and commit the transaction', async ({ page }) => {
        // 1. Setup: Login and create a portfolio and a target asset
        await page.goto('/');
        await page.getByLabel('Email address').fill('test@example.com');
        await page.getByLabel('Password').fill('Secure*123');
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByRole('button', { name: 'Create New Portfolio' }).click();
        await page.getByLabel('Portfolio Name').fill(portfolioName);
        await page.getByRole('button', { name: 'Create' }).click();
        await expect(page.getByText(portfolioName)).toBeVisible();

        // Get the portfolio ID from the URL
        const url = page.url();
        portfolioId = url.split('/').pop()!;
        expect(portfolioId).toBeDefined();

        // Create the target asset 'RELIANCE'
        await page.getByRole('button', { name: 'Add Transaction' }).click();
        await page.getByLabel('Asset').fill('RELIANCE');
        await page.getByRole('button', { name: "Create Asset 'RELIANCE'" }).click();
        await expect(page.getByText("Asset 'RELIANCE' created successfully.")).toBeVisible();
        await page.getByRole('button', { name: 'Cancel' }).click();

        // 2. Upload a file with an unrecognized symbol 'RIL'
        await page.getByRole('link', { name: 'Data Import' }).click();
        await expect(page.getByRole('heading', { name: 'Import Transactions' })).toBeVisible();

        const csvContent = 'ticker_symbol,transaction_type,quantity,price_per_unit,transaction_date,fees\nRIL,BUY,10,2800,2023-10-10,15.0';
        const file = new File([csvContent], 'unmapped.csv', { type: 'text/csv' });

        const fileChooserPromise = page.waitForEvent('filechooser');
        await page.getByLabel('Upload File').click();
        const fileChooser = await fileChooserPromise;
        await fileChooser.setFiles({
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
        const searchResult = page.locator('li', { hasText: 'RELIANCE' });
        await expect(searchResult).toBeVisible();
        await searchResult.click();
        await page.getByRole('button', { name: 'Save Mapping' }).click();

        // 5. Commit and Verify
        await expect(page.getByRole('heading', { name: 'New Transactions (1)' })).toBeVisible();
        const newTransactionRow = page.locator('tr', { hasText: 'RIL' });
        await expect(newTransactionRow).toBeVisible();

        await page.getByRole('button', { name: /Commit \d+ Transactions/ }).click();
        await expect(page.getByText('Successfully committed 1 transactions.')).toBeVisible();

        // Navigate to portfolio and verify transaction
        await page.waitForURL(`**/portfolios/${portfolioId}`);
        await expect(page.getByText('RELIANCE')).toBeVisible();
        await expect(page.getByText('10.00')).toBeVisible(); // Quantity
    });

    test('should automatically use the created alias for subsequent imports', async ({ page }) => {
        // 1. Navigate to import page again
        await page.getByRole('link', { name: 'Data Import' }).click();
        await expect(page.getByRole('heading', { name: 'Import Transactions' })).toBeVisible();

        // 2. Upload a new file with the same 'RIL' ticker
        const csvContent = 'ticker_symbol,transaction_type,quantity,price_per_unit,transaction_date,fees\nRIL,BUY,5,2900,2023-11-11,10.0';
        const file = new File([csvContent], 'mapped.csv', { type: 'text/csv' });

        const fileChooserPromise = page.waitForEvent('filechooser');
        await page.getByLabel('Upload File').click();
        const fileChooser = await fileChooserPromise;
        await fileChooser.setFiles({
            name: 'mapped.csv',
            mimeType: 'text/csv',
            buffer: Buffer.from(csvContent),
        });

        await page.getByRole('button', { name: 'Upload and Preview' }).click();

        // 3. Verify it appears directly in "New Transactions"
        await expect(page.getByRole('heading', { name: 'Transactions Needing Mapping (0)' })).toBeVisible();
        await expect(page.getByRole('heading', { name: 'New Transactions (1)' })).toBeVisible();
        const newTransactionRow = page.locator('tr', { hasText: 'RIL' });
        await expect(newTransactionRow).toBeVisible();
    });
});
