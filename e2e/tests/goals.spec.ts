import { test, expect, Page } from '@playwright/test';

const standardUser = {
  name: 'Goal User E2E',
  email: `goal.e2e.${Date.now()}@example.com`,
  password: 'Password123!',
};

const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('Goal Planning E2E Flow', () => {
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

  test('should allow a user to create a goal, link a portfolio, and see progress', async ({ page }) => {
    const portfolioName = `Goal Test Portfolio ${Date.now()}`;
    const goalName = `Buy a New Laptop`;

    // 1. Create a portfolio and add a transaction
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset').pressSequentially('AAPL');
    const createAssetButton = page.getByRole('button', { name: `Create Asset "AAPL"` });
    await expect(createAssetButton).toBeVisible();
    await createAssetButton.click();
    await page.getByLabel('Quantity').fill('10');
    await page.getByLabel('Price per Unit').fill('150'); // Total value = 1500
    await page.getByLabel('Date').fill('2023-01-15');
    await page.getByRole('button', { name: 'Save Transaction' }).click();
    await expect(page.getByRole('row', { name: /AAPL/ })).toBeVisible();

    // 2. Navigate to Goals page and create a new goal
    await page.getByRole('link', { name: 'Goals' }).click();
    await expect(page.getByRole('heading', { name: 'Financial Goals' })).toBeVisible();
    await page.getByRole('button', { name: 'Create New Goal' }).click();
    await page.getByLabel('Name').fill(goalName);
    await page.getByLabel('Target Amount').fill('2000');
    await page.getByLabel('Target Date').fill('2025-12-31');
    await page.getByRole('button', { name: 'Create Goal' }).click();
    await expect(page.getByRole('heading', { name: goalName })).toBeVisible();

    // 3. Link the portfolio to the goal
    const goalCard = page.locator('.card', { hasText: goalName });
    await page.getByTestId(`link-asset-button-${goal_res.json().id}`).click();
    const assetLinkModal = page.getByRole('dialog');
    await expect(assetLinkModal).toBeVisible();
    await assetLinkModal.getByRole('combobox').selectOption({ label: `${portfolioName} (Portfolio)` });
    await assetLinkModal.getByRole('button', { name: 'Link' }).click();
    await expect(assetLinkModal).not.toBeVisible();

    // 4. Verify progress
    await goalCard.getByRole('button', { name: 'Show Details' }).click();
    const detailView = goalCard.locator('.bg-gray-100');
    await expect(detailView).toBeVisible();

    // Total value of portfolio is ~1500. Goal target is 2000. Progress should be ~75%.
    await expect(detailView.getByText(/75.00% Complete/)).toBeVisible();
  });
});
