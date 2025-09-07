import { test, expect } from '@playwright/test';

const standardUser = {
  name: 'RD User E2E',
  email: `rd.e2e.${Date.now()}@example.com`,
  password: 'Password123!',
};

const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('Recurring Deposit E2E Flow', () => {
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

  test('should allow a user to create, view, and delete a recurring deposit', async ({ page }) => {
    const portfolioName = `My RD Portfolio ${Date.now()}`;
    const rdName = 'My Test RD';

    // 1. Create a portfolio
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // 2. Add a Recurring Deposit
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset Type').selectOption('Recurring Deposit');

    await page.getByLabel('Institution Name').fill(rdName);
    await page.getByLabel('Monthly Installment').fill('5000');
    await page.getByLabel('Interest Rate (%)').fill('7.5');
    await page.getByLabel('Start Date').fill('2023-01-01');
    await page.getByLabel('Tenure (in months)').fill('12');

    await page.getByRole('button', { name: 'Save Transaction' }).click();

    // 3. Verify the new RD appears in the HoldingsTable
    const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
    await expect(holdingsTable).toBeVisible();
    const rdRow = holdingsTable.getByRole('row', { name: new RegExp(rdName) });
    await expect(rdRow).toBeVisible();

    // 4. Click on the RD to open the detail modal
    await rdRow.click();
    await expect(page.getByRole('heading', { name: `Holding Detail: ${rdName}` })).toBeVisible();

    // 5. Verify details in the modal
    await expect(page.locator('.modal-content')).toContainText('Monthly Installment');
    await expect(page.locator('.modal-content')).toContainText('5,000');

    // 6. Delete the RD
    await page.getByRole('button', { name: 'Delete RD' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.getByRole('dialog').getByRole('button', { name: 'Delete' }).click();

    // 7. Verify deletion
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();
    await expect(rdRow).not.toBeVisible();
  });
});
