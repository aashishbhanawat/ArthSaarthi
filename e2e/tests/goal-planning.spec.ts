import { test, expect } from '@playwright/test';
import { login } from '../utils/login';

const standardUser = {
  email: `goal-user.${Date.now()}@example.com`,
  password: 'Password123!',
};

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
  password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('Goal Planning & Tracking Feature', () => {
  // Create a dedicated user for this test suite to avoid state pollution
  test.beforeAll(async ({ request }) => {
    const adminLoginResponse = await request.post('/api/v1/auth/login', {
      form: { username: adminUser.email, password: adminUser.password },
    });
    expect(adminLoginResponse.ok()).toBeTruthy();
    const { access_token } = await adminLoginResponse.json();
    const adminAuthHeaders = { Authorization: `Bearer ${access_token}` };

    const userCreateResponse = await request.post('/api/v1/users/', {
      headers: adminAuthHeaders,
      data: { ...standardUser, is_admin: false },
    });
    expect(userCreateResponse.ok()).toBeTruthy();
  });

  test.beforeEach(async ({ page }) => {
    await login(page, standardUser.email, standardUser.password);
  });

  test('User can create, view, link, edit, and delete a financial goal', async ({ page }) => {
    const goalName = 'Retirement Fund';
    const updatedGoalName = 'Early Retirement Fund';
    const targetAmount = '1000000';
    const portfolioName = `Goal Test Portfolio ${Date.now()}`;

    // --- 1. Create a portfolio to link later ---
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await expect(page.getByRole('heading', { name: 'Create Portfolio' })).toBeVisible();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible({ timeout: 10000 });

    // Add a transaction to the portfolio so it has value for progress calculation
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset').pressSequentially('MSFT');
    await page.getByRole('button', { name: 'Create Asset "MSFT"' }).click();
    await page.getByLabel('Quantity').fill('10');
    await page.getByLabel('Price per Unit').fill('200');
    await page.getByLabel('Date').fill('2023-01-01');
    await page.getByRole('button', { name: 'Save Transaction' }).click();
    await expect(page.getByRole('row', { name: /MSFT/ })).toBeVisible();


    // --- 2. Create a new goal ---
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


    // --- 3. Navigate to Detail Page and Link the Portfolio ---
    await goalCard.click();
    await expect(page.getByRole('heading', { name: goalName })).toBeVisible();

    await page.getByRole('button', { name: 'Link Asset/Portfolio' }).click();
    await expect(page.getByRole('heading', { name: 'Link to Goal' })).toBeVisible();

    await page.getByRole('listitem').filter({ hasText: portfolioName }).click();
    await page.getByRole('button', { name: 'Link', exact: true }).click();

    await expect(page.getByRole('heading', { name: 'Link to Goal' })).not.toBeVisible();

    const linkedItemsSection = page.locator('section[aria-labelledby="linked-items-header"]');
    await expect(linkedItemsSection.getByText(portfolioName)).toBeVisible();


    // --- 4. Verify Progress Update ---
    await expect(page.getByText('₹0.00 /')).not.toBeVisible();

    await page.getByRole('link', { name: 'Goals' }).click();
    await expect(page.getByRole('heading', { name: 'Financial Goals' })).toBeVisible();

    const updatedGoalCard = page.locator('div.flex.justify-between.items-start', { hasText: goalName });
    await expect(updatedGoalCard.getByText('0.00%')).not.toBeVisible();


    // --- 5. Edit the Goal ---
    await updatedGoalCard.getByRole('button', { name: 'Edit' }).click();
    await expect(page.getByRole('heading', { name: 'Edit Goal' })).toBeVisible();
    await page.getByLabel('Goal Name').fill(updatedGoalName);
    await page.getByRole('button', { name: 'Save', exact: true }).click();

    await page.waitForResponse(resp => resp.url().includes('/api/v1/goals') && resp.status() === 200);
    const finalGoalCard = page.locator('div.flex.justify-between.items-start', { hasText: updatedGoalName });
    await expect(finalGoalCard).toBeVisible();


    // --- 6. Delete the Goal ---
    await finalGoalCard.getByRole('button', { name: 'Delete' }).click();
    await expect(page.getByRole('heading', { name: 'Delete Goal' })).toBeVisible();
    await page.getByRole('button', { name: 'Delete' }).click();

    await page.waitForResponse(resp => resp.url().includes('/api/v1/goals') && resp.status() === 200);
    await expect(finalGoalCard).not.toBeVisible();
    await expect(page.getByText("You haven't set any goals yet.")).toBeVisible();
  });
});
