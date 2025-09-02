import { test, expect, Page } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const standardUser = {
  name: 'Standard User E2E',
  email: `standard.e2e.${Date.now()}@example.com`,
  password: 'Password123!',
};

const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('Automated Data Import E2E Test', () => {
    test.slow();
    const portfolioName = `Test Import Portfolio ${Date.now()}`;
    const csvFilePath = path.join(__dirname, 'temp_transactions.csv');
    const csvContent = `ticker_symbol,transaction_type,quantity,price_per_unit,transaction_date,fees\nNTPC,BUY,10,150.75,2023-10-26,5.50\nSCI,BUY,5,170.25,2023-10-27,2.75`;

    // Create the temp CSV file before tests run, and clean it up after.
    test.beforeAll(() => {
        fs.writeFileSync(csvFilePath, csvContent);
    });

    test.afterAll(() => {
        if (fs.existsSync(csvFilePath)) {
            fs.unlinkSync(csvFilePath);
        }
    });

    test.beforeAll(async ({ request }) => {
        // The global setup has already created the admin user.
        // We just need to log in as admin to create our test-specific standard user and assets.
        const adminLoginResponse = await request.post('/api/v1/auth/login', {
          form: { username: adminUser.email, password: adminUser.password },
        });
        expect(adminLoginResponse.ok()).toBeTruthy();
        const { access_token } = await adminLoginResponse.json();
        const adminAuthHeaders = { Authorization: `Bearer ${access_token}` };

        // Create Standard User via API (as Admin)
        const standardUserCreateResponse = await request.post('/api/v1/users/', {
          headers: adminAuthHeaders,
          data: { ...standardUser, is_admin: false },
        });
        expect(standardUserCreateResponse.ok()).toBeTruthy();

        // Create necessary assets for the import test (as Admin)
        const assetsToCreate = [
            { ticker_symbol: 'NTPC', name: 'NTPC Ltd', asset_type: 'Stock', currency: 'INR', exchange: 'NSE' },
            { ticker_symbol: 'SCI', name: 'Shipping Corporation of India', asset_type: 'Stock', currency: 'INR', exchange: 'NSE' },
        ];

        for (const asset of assetsToCreate) {
            const assetCreateResponse = await request.post('/api/v1/assets/', {
                headers: adminAuthHeaders,                data: { ...asset, asset_type: 'STOCK' }
            });
            if (!assetCreateResponse.ok()) {
                console.error(`[DEBUG] Failed to create asset ${asset.ticker_symbol}: ${await assetCreateResponse.text()}`);
            }
            expect(assetCreateResponse.ok()).toBeTruthy();
        }
      });

      test.beforeEach(async ({ page }) => {
        // Login as the standard user before each test
        await page.goto('/');
        await page.getByLabel('Email address').fill(standardUser.email);
        await page.getByLabel('Password').fill(standardUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
      });

    test('should allow a user to upload, preview, and commit a CSV of transactions', async ({ page }) => {

        // Create a portfolio to import into
        await page.getByRole('link', { name: 'Portfolios' }).click();
        await expect(page.getByRole('heading', { name: 'Portfolios' })).toBeVisible();
        await page.getByRole('button', { name: 'Create New Portfolio' }).click();
        await expect(page.getByRole('heading', { name: 'Create New Portfolio' })).toBeVisible();
        await page.getByLabel('Portfolio Name').fill(portfolioName);
        await page.getByRole('button', { name: 'Create', exact: true }).click();
        await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible(); // Wait for navigation

        // Navigate to Import Page and upload the file
        await page.getByRole('link', { name: 'Import' }).click();
        await expect(page.getByRole('heading', { name: 'Import Transactions' })).toBeVisible();
        await page.getByLabel('Select Portfolio').selectOption({ label: portfolioName });
        await page.getByLabel('Statement Type').selectOption({ value: 'Generic CSV' });
        // Use setInputFiles for a more robust file upload interaction, avoiding click interception issues.
        await page.getByLabel('Upload a file').setInputFiles(csvFilePath);
        await page.getByRole('button', { name: 'Upload and Preview' }).click();

        // Verify the Preview Page and Commit
        await expect(page.getByRole('heading', { name: 'Import Preview' })).toBeVisible();
        await expect(page.getByText(/New Transactions \(\d+\)/)).toBeVisible();
        await expect(page.getByRole('cell', { name: 'NTPC' })).toBeVisible();
        await page.getByRole('button', { name: /Commit 2 Transactions/ }).click();
        await expect(page.getByText('Successfully committed 2 transactions.')).toBeVisible();

        // Verify the transactions on the portfolio detail page
        await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible({ timeout: 5000 });
        const transactionList = page.locator('.table-auto');
        await expect(transactionList.getByText('NTPC', { exact: true })).toBeVisible();
        await expect(transactionList.getByText('SCI', { exact: true })).toBeVisible();
    });
});