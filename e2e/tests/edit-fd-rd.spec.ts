import { test, expect } from '@playwright/test';

const standardUser = {
  name: 'Edit FD RD User',
  email: `edit.fdrd.${Date.now()}@example.com`,
  password: 'Password123!',
};

const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('Edit FD and RD Flow', () => {
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

  test('should allow editing Fixed Deposit and Recurring Deposit details', async ({ page }) => {
    const portfolioName = `Edit Test Portfolio ${Date.now()}`;
    const fdName = 'FD to Edit';
    const rdName = 'RD to Edit';

    // 1. Create a portfolio
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // Get portfolio ID
    const url = page.url();
    const portfolioId = url.split('/').pop()!;

    // --- FIXED DEPOSIT ---

    // 2. Add a Fixed Deposit
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByText('Standard Transaction').click();
    await page.getByLabel('Asset Type').selectOption('Fixed Deposit');

    await page.getByLabel('Institution Name').fill(fdName);
    await page.getByLabel('Principal Amount').fill('10000');
    await page.getByLabel('Interest Rate (%)').fill('7.0');
    await page.getByLabel('Start Date').fill(new Date().toISOString().split('T')[0]);
    await page.getByLabel('Maturity Date').fill(new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]);

    const holdingsResponsePromise = page.waitForResponse(resp => resp.url().includes(`/api/v1/portfolios/${portfolioId}/holdings`));
    await page.getByRole('button', { name: 'Save Transaction' }).click();
    await holdingsResponsePromise;

    // Verify created
    const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
    await expect(holdingsTable.getByRole('row', { name: fdName })).toBeVisible();

    // 3. Edit FD
    await holdingsTable.getByRole('row', { name: fdName }).click();
    await expect(page.getByRole('heading', { name: `Holding Detail: ${fdName}` })).toBeVisible();

    // Wait for details to load (edit button is disabled until loaded)
    await expect(page.getByRole('button', { name: 'Edit FD Details' })).toBeEnabled();
    await page.getByRole('button', { name: 'Edit FD Details' }).click();

    // Verify form is populated
    await expect(page.getByRole('heading', { name: 'Edit Transaction' })).toBeVisible();
    await expect(page.getByLabel('Institution Name')).toHaveValue(fdName);
    await expect(page.getByLabel('Principal Amount')).toHaveValue('10000');

    // Change Principal Amount
    await page.getByLabel('Principal Amount').fill('15000');
    await page.getByRole('button', { name: 'Save Changes' }).click();

    const errorAlert = page.locator('.alert-error');
    if (await errorAlert.isVisible()) {
        console.log('Error Alert content:', await errorAlert.textContent());
    }

    // Transaction modal closes, Detail modal was closed before opening transaction modal.
    // We need to re-open the detail modal to verify changes.
    await expect(page.getByRole('heading', { name: 'Edit Transaction' })).not.toBeVisible();

    // Re-open FD details
    await holdingsTable.getByRole('row', { name: fdName }).click();
    await expect(page.getByRole('heading', { name: `Holding Detail: ${fdName}` })).toBeVisible();

    // Check value in modal
    await expect(page.locator('[data-testid="fd-details-section"]')).toContainText('15,000');

    // Close modal
    await page.locator('.modal-content').locator('button').first().click();

    // Wait for modal to close
    await expect(page.getByRole('heading', { name: `Holding Detail: ${fdName}` })).not.toBeVisible();

    // --- RECURRING DEPOSIT ---

    // 4. Add Recurring Deposit
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByText('Standard Transaction').click();
    await page.getByLabel('Asset Type').selectOption('Recurring Deposit');

    await page.getByLabel('Institution Name').fill(rdName);
    await page.getByLabel('Monthly Installment').fill('2000');
    await page.getByLabel('Interest Rate (%)').fill('6.5');
    await page.getByLabel('Start Date').fill(new Date().toISOString().split('T')[0]);
    await page.getByLabel('Tenure (in months)').fill('24');

    const holdingsResponsePromise2 = page.waitForResponse(resp => resp.url().includes(`/api/v1/portfolios/${portfolioId}/holdings`));
    await page.getByRole('button', { name: 'Save Transaction' }).click();
    await holdingsResponsePromise2;

    // Verify created
    await expect(holdingsTable.getByRole('row', { name: rdName })).toBeVisible();

    // 5. Edit RD
    await holdingsTable.getByRole('row', { name: rdName }).click();
    await expect(page.getByRole('heading', { name: `Holding Detail: ${rdName}` })).toBeVisible();

    await expect(page.getByRole('button', { name: 'Edit RD Details' })).toBeEnabled();
    await page.getByRole('button', { name: 'Edit RD Details' }).click();

    // Verify form populated
    await expect(page.getByRole('heading', { name: 'Edit Transaction' })).toBeVisible();
    await expect(page.getByLabel('Institution Name')).toHaveValue(rdName);
    await expect(page.getByLabel('Monthly Installment')).toHaveValue('2000');

    // Change Monthly Installment
    await page.getByLabel('Monthly Installment').fill('2500');
    await page.getByRole('button', { name: 'Save Changes' }).click();

    // Re-open RD details
    await expect(page.getByRole('heading', { name: 'Edit Transaction' })).not.toBeVisible();
    await holdingsTable.getByRole('row', { name: rdName }).click();
    await expect(page.getByRole('heading', { name: `Holding Detail: ${rdName}` })).toBeVisible();

    // Verify update
    await expect(page.locator('[data-testid="rd-details-section"]')).toContainText('2,500');

  });
});
