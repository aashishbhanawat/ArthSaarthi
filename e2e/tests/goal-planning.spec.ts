import { test, expect } from '@playwright/test';
import { login } from '../utils/login';

const standardUser = {
  email: `goal-user-final-${Date.now()}@example.com`,
  password: 'Password123!',
};

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
  password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('Goal Planning & Tracking Feature', () => {
  let userAuthHeaders: { [key: string]: string };
  let portfolioId: string;
  const portfolioName = `Goal Test Portfolio ${Date.now()}`;

  // Setup: Create a user and a portfolio with a transaction via API
  test.beforeAll(async ({ request }) => {
    // 1. Get Admin Token
    const adminLoginResponse = await request.post('/api/v1/auth/login', {
      form: { username: adminUser.email, password: adminUser.password },
    });
    expect(adminLoginResponse.ok()).toBeTruthy();
    const { access_token: adminToken } = await adminLoginResponse.json();
    const adminAuthHeaders = { Authorization: `Bearer ${adminToken}` };

    // 2. Create Standard User
    const userCreateResponse = await request.post('/api/v1/users/', {
      headers: adminAuthHeaders,
      data: { ...standardUser, is_admin: false },
    });
    expect(userCreateResponse.ok()).toBeTruthy();

    // 3. Login as Standard User to get their token
    const userLoginResponse = await request.post('/api/v1/auth/login', {
      form: { username: standardUser.email, password: standardUser.password },
    });
    expect(userLoginResponse.ok()).toBeTruthy();
    const { access_token: userToken } = await userLoginResponse.json();
    userAuthHeaders = { Authorization: `Bearer ${userToken}` };

    // 4. Create Portfolio for the new user
    const portfolioCreateResponse = await request.post('/api/v1/portfolios/', {
      headers: userAuthHeaders,
      data: { name: portfolioName, description: 'For Goal E2E test' },
    });
    expect(portfolioCreateResponse.ok()).toBeTruthy();
    const portfolio = await portfolioCreateResponse.json();
    portfolioId = portfolio.id;

    // 5. Create an Asset and a Transaction to give the portfolio value
    const assetResponse = await request.post('/api/v1/assets/', {
        headers: userAuthHeaders,
        data: { ticker_symbol: 'GOALTEST', name: 'Goal Test Asset', asset_type: 'STOCK' },
    });
    expect(assetResponse.ok()).toBeTruthy();
    const asset = await assetResponse.json();

    const txnResponse = await request.post(`/api/v1/portfolios/${portfolioId}/transactions/`, {
        headers: userAuthHeaders,
        data: { asset_id: asset.id, transaction_type: 'BUY', quantity: 10, price_per_unit: 100, transaction_date: new Date().toISOString(), fees: 1 },
    });
    expect(txnResponse.ok()).toBeTruthy();
  });

  test.beforeEach(async ({ page }) => {
    await login(page, standardUser.email, standardUser.password);
  });

  test('User can create, view, link, edit, and delete a financial goal', async ({ page }) => {
    const goalName = 'Retirement Fund';
    const updatedGoalName = 'Early Retirement Fund';
    const targetAmount = '1000000';

    // --- 1. Create a new goal ---
    await page.getByRole('link', { name: 'Goals' }).click();
    await expect(page.getByRole('heading', { name: 'Financial Goals' })).toBeVisible();
    await page.getByRole('button', { name: 'Create New Goal' }).click();
    await expect(page.getByRole('heading', { name: 'Create New Goal' })).toBeVisible();

    await page.getByLabel('Goal Name').fill(goalName);
    await page.getByLabel('Target Amount').fill(targetAmount);
    await page.getByLabel('Target Date').fill('2050-01-01');
    await page.getByRole('button', { name: 'Save', exact: true }).click();

    await page.waitForResponse(resp => resp.url().includes('/api/v1/goals') && resp.status() === 200);

    const goalCard = page.locator('div.flex.justify-between.items-start', { hasText: goalName });
    await expect(goalCard).toBeVisible();
    await expect(goalCard.getByText('0.00%')).toBeVisible();

    // --- 2. Navigate to Detail Page and Link the Portfolio ---
    await goalCard.click();
    await expect(page.getByRole('heading', { name: goalName })).toBeVisible();

    await page.getByRole('button', { name: 'Link Asset/Portfolio' }).click();
    await expect(page.getByRole('heading', { name: 'Link to Goal' })).toBeVisible();

    await page.getByRole('listitem').filter({ hasText: portfolioName }).click();
    await page.getByRole('button', { name: 'Link', exact: true }).click();

    await expect(page.getByRole('heading', { name: 'Link to Goal' })).not.toBeVisible();

    const linkedItemsSection = page.locator('section[aria-labelledby="linked-items-header"]');
    await expect(linkedItemsSection.getByText(portfolioName)).toBeVisible();

    // --- 3. Verify Progress Update ---
    await expect(page.getByText('₹0.00 /')).not.toBeVisible();

    await page.getByRole('link', { name: 'Goals' }).click();
    await expect(page.getByRole('heading', { name: 'Financial Goals' })).toBeVisible();

    const updatedGoalCard = page.locator('div.flex.justify-between.items-start', { hasText: goalName });
    await expect(updatedGoalCard.getByText('0.00%')).not.toBeVisible();

    // --- 4. Edit the Goal ---
    await updatedGoalCard.getByRole('button', { name: 'Edit' }).click();
    await expect(page.getByRole('heading', { name: 'Edit Goal' })).toBeVisible();
    await page.getByLabel('Goal Name').fill(updatedGoalName);
    await page.getByRole('button', { name: 'Save', exact: true }).click();

    await page.waitForResponse(resp => resp.url().includes('/api/v1/goals') && resp.status() === 200);
    const finalGoalCard = page.locator('div.flex.justify-between.items-start', { hasText: updatedGoalName });
    await expect(finalGoalCard).toBeVisible();

    // --- 5. Delete the Goal ---
    await finalGoalCard.getByRole('button', { name: 'Delete' }).click();
    await expect(page.getByRole('heading', { name: 'Delete Goal' })).toBeVisible();
    await page.getByRole('button', { name: 'Delete' }).click();

    await page.waitForResponse(resp => resp.url().includes('/api/v1/goals') && resp.status() === 200);
    await expect(finalGoalCard).not.toBeVisible();
    await expect(page.getByText("You haven't set any goals yet.")).toBeVisible();
  });
});
