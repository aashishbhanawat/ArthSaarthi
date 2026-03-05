import { test, expect, Page } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const standardUser = {
    name: 'FD Import User',
    email: `fd.import.${Date.now()}@example.com`,
    password: 'Password123!',
};

const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('FD Data Import E2E Test', () => {
    test.slow();
    const portfolioName = `FD Test Portfolio ${Date.now()}`;
    const dummyPdfPath = path.join(__dirname, 'temp_fd_statement.pdf');

    test.beforeAll(() => {
        // Create a dummy PDF file for testing upload (content format doesn't matter for the upload dialog test)
        fs.writeFileSync(dummyPdfPath, 'dummy pdf content for E2E');
    });

    test.afterAll(() => {
        if (fs.existsSync(dummyPdfPath)) {
            fs.unlinkSync(dummyPdfPath);
        }
    });

    test.beforeAll(async ({ request }) => {
        const adminLoginResponse = await request.post('/api/v1/auth/login', {
            form: { username: adminUser.email, password: adminUser.password },
        });
        expect(adminLoginResponse.ok()).toBeTruthy();
        const { access_token } = await adminLoginResponse.json();
        const adminAuthHeaders = { Authorization: `Bearer ${access_token}` };

        // Create Standard User
        const standardUserCreateResponse = await request.post('/api/v1/users/', {
            headers: adminAuthHeaders,
            data: { ...standardUser, is_admin: false },
        });
        expect(standardUserCreateResponse.ok()).toBeTruthy();
    });

    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(standardUser.email);
        await page.getByLabel('Password', { exact: true }).fill(standardUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
    });

    test('should show error or password modal for FD upload', async ({ page }) => {
        // Create a portfolio to import into
        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByRole('button', { name: 'Create New Portfolio' }).click();
        await page.getByLabel('Portfolio Name').fill(portfolioName);
        await page.getByRole('button', { name: 'Create', exact: true }).click();
        await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

        // Navigate to Import Page and upload the file
        await page.getByRole('link', { name: 'Import' }).click();
        await expect(page.getByRole('heading', { name: 'Import Transactions' })).toBeVisible();
        await page.getByLabel('Select Portfolio').selectOption({ label: portfolioName });
        await page.getByLabel('Statement Type').selectOption({ value: 'SBI FD Statement' });
        await page.getByLabel('Upload a file').setInputFiles(dummyPdfPath);
        await page.getByRole('button', { name: 'Upload and Preview' }).click();

        // The parser will fail because it's a dummy PDF, not a real SBI statement.
        // It might show an error alert, or if the backend throws an error, the frontend shows it.
        // Either way, we just verify the upload goes through and error handling works.
        await expect(page.locator('.alert-error')).toBeVisible({ timeout: 15000 });
    });
});
