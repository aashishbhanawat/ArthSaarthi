import { test, expect } from '@playwright/test';

test.describe.serial('Advanced Asset E2E Flow', () => {
    const standardUser = {
        name: 'Advanced Asset User',
        email: `adv.asset.e2e.${Date.now()}@example.com`,
        password: 'Password123!',
    };
    const adminUser = {
        email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
        password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
    };

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

    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(standardUser.email);
        await page.getByLabel('Password').fill(standardUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
    });

    test('should allow a user to add a Fixed Deposit', async ({ page }) => {
        const portfolioName = `My FD Portfolio ${Date.now()}`;

        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByRole('button', { name: 'Create New Portfolio' }).click();
        await page.getByLabel('Name').fill(portfolioName);
        await page.getByRole('button', { name: 'Create', exact: true }).click();
        await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

        await page.getByRole('button', { name: 'Add Fixed Income' }).click();
        await page.getByRole('button', { name: 'Fixed Deposit' }).click();

        await page.getByLabel('Institution Name').fill('E2E Test Bank');
        await page.getByLabel('Principal Amount').fill('100000');
        await page.getByLabel('Interest Rate (%)').fill('7.5');
        await page.getByLabel('Start Date').fill('2023-01-01');
        await page.getByLabel('Maturity Date').fill('2024-01-01');
        await page.getByLabel('Payout Type').selectOption('REINVESTMENT');
        await page.getByLabel('Compounding Frequency').selectOption('QUARTERLY');
        await page.getByRole('button', { name: 'Save Fixed Deposit' }).click();

        const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
        await expect(holdingsTable).toBeVisible();
        const fdRow = holdingsTable.getByRole('row', { name: /E2E Test Bank FD/ });
        await expect(fdRow).toBeVisible();
        await expect(fdRow.getByRole('cell', { name: '7.50%' })).toBeVisible();
    });

    test('should allow a user to add a Bond', async ({ page }) => {
        const portfolioName = `My Bond Portfolio ${Date.now()}`;

        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByRole('button', { name: 'Create New Portfolio' }).click();
        await page.getByLabel('Name').fill(portfolioName);
        await page.getByRole('button', { name: 'Create', exact: true }).click();
        await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

        await page.getByRole('button', { name: 'Add Fixed Income' }).click();
        await page.getByRole('button', { name: 'Bond' }).click();

        await page.getByLabel('Bond Name').fill('E2E Test Bond');
        await page.getByLabel('Face Value').fill('1000');
        await page.getByLabel('Coupon Rate (%)').fill('8');
        await page.getByLabel('Purchase Price').fill('1010');
        await page.getByLabel('Purchase Date').fill('2023-01-01');
        await page.getByLabel('Maturity Date').fill('2030-01-01');
        await page.getByLabel('Interest Payout').selectOption('ANNUALLY');
        await page.getByLabel('Quantity').fill('10');
        await page.getByRole('button', { name: 'Save Bond' }).click();

        const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
        await expect(holdingsTable).toBeVisible();
        const bondRow = holdingsTable.getByRole('row', { name: /E2E Test Bond/ });
        await expect(bondRow).toBeVisible();
        await expect(bondRow.getByRole('cell', { name: '8.00%' })).toBeVisible();
    });

    test('should allow a user to add a PPF Account', async ({ page }) => {
        const portfolioName = `My PPF Portfolio ${Date.now()}`;

        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByRole('button', { name: 'Create New Portfolio' }).click();
        await page.getByLabel('Name').fill(portfolioName);
        await page.getByRole('button', { name: 'Create', exact: true }).click();
        await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

        await page.getByRole('button', { name: 'Add Fixed Income' }).click();
        await page.getByRole('button', { name: 'PPF Account' }).click();

        await page.getByLabel('Institution Name').fill('E2E Test Post Office');
        await page.getByLabel('Opening Date').fill('2020-01-01');
        await page.getByLabel('Current Balance').fill('50000');
        await page.getByRole('button', { name: 'Save PPF Account' }).click();

        const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
        await expect(holdingsTable).toBeVisible();
        const ppfRow = holdingsTable.getByRole('row', { name: /PPF Account/ });
        await expect(ppfRow).toBeVisible();
    });
});
