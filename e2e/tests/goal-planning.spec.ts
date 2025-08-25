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
    // This is necessary because the new user doesn't have any portfolios by default.
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    // Wait for navigation to the new portfolio's detail page to confirm creation
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible({ timeout: 10000 });


    // --- 2. Create a new goal ---
    await page.getByRole('link', { name: 'Goals' }).click();
    await expect(page.getByRole('heading', { name: 'Financial Goals' })).toBeVisible();
    await page.getByRole('button', { name: 'Create New Goal' }).click();
    await expect(page.getByRole('heading', { name: 'Create New Goal' })).toBeVisible();

    await page.getByLabel('Goal Name').fill(goalName);
    await page.getByLabel('Target Amount').fill(targetAmount);
    await page.getByLabel('Target Date').fill('2050-01-01');
    await page.getByRole('button', { name: 'Save', exact: true }).click();

    // Wait for the goals list to be re-fetched after creation
    await page.waitForResponse(response =>
      response.url().includes('/api/v1/goals') && response.request().method() === 'GET'
    );

    // Now the UI should be updated.
    const goalCard = page.locator('.bg-card').filter({ hasText: goalName });
    await expect(goalCard).toBeVisible();
    await expect(goalCard.getByText('0%')).toBeVisible();
    await expect(goalCard.getByText(`of ₹${Number(targetAmount).toLocaleString('en-IN')}`)).toBeVisible();


    // --- 2. Navigate to Detail Page and Link a Portfolio ---
    await goalCard.click();
    await expect(page.getByRole('heading', { name: goalName })).toBeVisible();

    // Link a portfolio
    await page.getByRole('button', { name: 'Link Asset/Portfolio' }).click();
    await expect(page.getByRole('heading', { name: 'Link to Goal' })).toBeVisible();

    // The test DB creates a "Tech Giants" portfolio
    const portfolioToLink = page.locator('.bg-card').filter({ hasText: 'Tech Giants' });
    await portfolioToLink.getByRole('button', { name: 'Link' }).click();

    await expect(page.getByRole('heading', { name: 'Link to Goal' })).not.toBeVisible(); // Modal should close

    // Verify the portfolio is now in the "Linked Items" list
    const linkedItemsSection = page.locator('section[aria-labelledby="linked-items-header"]');
    await expect(linkedItemsSection.getByText('Tech Giants')).toBeVisible();


    // --- 3. Verify Progress Update ---
    // Progress on detail page should be updated (we'll check it's not the initial state)
    await expect(page.getByText('₹0 /')).not.toBeVisible();

    // Navigate back to goals list
    await page.getByRole('link', { name: 'Goals' }).click();
    await expect(page.getByRole('heading', { name: 'Financial Goals' })).toBeVisible();

    // HACK: Force a reload to bypass a potential React Query caching issue.
    await page.reload();
    await page.waitForResponse(response => response.url().includes('/api/v1/goals'));


    // Verify progress on the card is also updated
    const updatedGoalCard = page.locator('.bg-card').filter({ hasText: goalName });
    await expect(updatedGoalCard.getByText('0%')).not.toBeVisible();


    // --- 4. Edit the Goal ---
    await updatedGoalCard.getByRole('button', { name: 'Edit Goal' }).click();
    await expect(page.getByRole('heading', { name: 'Edit Goal' })).toBeVisible();
    await page.getByLabel('Goal Name').fill(updatedGoalName);
    await page.getByRole('button', { name: 'Save', exact: true }).click();

    // Verify the name has been updated
    await expect(page.locator('.bg-card').filter({ hasText: goalName })).not.toBeVisible();
    const finalGoalCard = page.locator('.bg-card').filter({ hasText: updatedGoalName });
    await expect(finalGoalCard).toBeVisible();


    // --- 5. Delete the Goal ---
    await finalGoalCard.getByRole('button', { name: 'Delete Goal' }).click();
    await expect(page.getByRole('heading', { name: 'Delete Goal' })).toBeVisible();
    await page.getByRole('button', { name: 'Delete' }).click();

    // Verify the card is gone
    await expect(finalGoalCard).not.toBeVisible();
    await expect(page.getByText('No goals found.')).toBeVisible();
  });
});
