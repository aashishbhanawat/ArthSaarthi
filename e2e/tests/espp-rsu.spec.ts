import { test, expect } from '@playwright/test';

const standardUser = {
  name: 'Standard User E2E',
  email: `standard.e2e.rsu.${Date.now()}@example.com`,
  password: 'Password123!',
};

const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('ESPP and RSU Flow', () => {
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

  test('should allow adding an RSU award with Sell to Cover', async ({ page }) => {
    const portfolioName = `RSU Portfolio ${Date.now()}`;
    const assetName = 'GOOGL';

    // 1. Create Portfolio
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // 2. Open Add Award Modal via Dropdown
    await page.getByRole('button', { name: 'Additional actions' }).click();
    // Wait for dropdown
    await expect(page.getByText('Add ESPP/RSU Award')).toBeVisible();
    await page.getByText('Add ESPP/RSU Award').click();
    await expect(page.getByRole('heading', { name: 'Add ESPP/RSU Award' })).toBeVisible();

    // 3. Fill Form
    // Asset Search
    await page.getByPlaceholder('Search ticker').fill(assetName);
    const listItem = page.locator(`li:has-text("${assetName}")`);
    await expect(listItem).toBeVisible();
    await listItem.click();

    // Dates & Quantity
    await page.getByLabel('Vest Date').fill(new Date().toISOString().split('T')[0]);
    await page.getByLabel('Quantity').fill('10');

    // Check price is 0 and read-only
    const priceInput = page.getByLabel('Cost (0 for RSU)');
    await expect(priceInput).toHaveValue('0');
    await expect(priceInput).not.toBeEditable();

    await page.getByLabel('FMV at Vest').fill('150');

    // Sell to Cover
    await page.getByLabel("Record 'Sell to Cover' for taxes").check();
    await page.getByLabel('Shares Sold').fill('4');
    await page.getByLabel('Sale Price').fill('150');

    // Submit
    await page.getByRole('button', { name: 'Add Award' }).click();

    // 4. Verify Transactions
    // Wait for modal to close
    await expect(page.getByRole('heading', { name: 'Add ESPP/RSU Award' })).not.toBeVisible();

    // Go to Transaction History
    await page.getByRole('link', { name: 'View History' }).click();

    // Check for RSU_VEST
    const rsuRow = page.getByRole('row', { name: /RSU_VEST/ });
    await expect(rsuRow).toBeVisible();
    await expect(rsuRow).toContainText('10'); // Quantity

    // Check for SELL
    const sellRow = page.getByRole('row', { name: /SELL/ });
    await expect(sellRow).toBeVisible();
    await expect(sellRow).toContainText('4'); // Quantity

    // Check for standard ADD button functionality (Regression)
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByText(portfolioName).click();

    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await expect(page.getByRole('heading', { name: 'Add Transaction' })).toBeVisible();
    // Close it
    await page.getByRole('button', { name: 'Cancel' }).click();
  });
});
