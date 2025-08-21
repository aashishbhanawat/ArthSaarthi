import { test, expect, Page } from '@playwright/test';
import { createPortfolio, createGoal, createAsset, createTransaction } from '../utils';
import { faker } from '@faker-js/faker';

test.describe.configure({ mode: 'parallel' });

const standardUser = {
  email: faker.internet.email(),
  password: 'password',
};

test.describe('Goal Planning E2E Flow', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    const apiContext = await browser.newContext();
    const api = apiContext.request;
    const standardUserCreateResponse = await api.post('/api/v1/users/', {
      data: { email: standardUser.email, password: standardUser.password, is_admin: false },
    });
    expect(standardUserCreateResponse.ok()).toBeTruthy();
    await apiContext.dispose();
  });

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    // Login as the standard user before each test
    await page.goto('/');
    await page.getByLabel('Email address').fill(standardUser.email);
    await page.getByLabel('Password').fill(standardUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await page.waitForURL('**/dashboard', { timeout: 30000 });
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('should allow a user to create a goal, link a portfolio, and see progress', async ({
    page,
  }) => {
    const portfolioName = `Goal Test Portfolio ${faker.string.uuid()}`;
    const goalName = `Buy a New Laptop`;

    // 1. Create a portfolio and add a transaction
    const portfolio = await createPortfolio(page.request, portfolioName, 'USD');
    const asset = await createAsset(page.request, 'AAPL', 'Apple Inc.', 'STOCK', 'USD', 'NASDAQ');
    await createTransaction(page.request, portfolio.id, asset.id, 'BUY', 10, 150, new Date().toISOString().split('T')[0]);

    // 2. Navigate to Goals page and create a new goal
    await page.goto('/goals');
    await expect(page.getByRole('heading', { name: 'Financial Goals' })).toBeVisible();

    const goal = await createGoal(page.request, goalName, 2000, '2025-12-31');

    await page.reload();

    await page.waitForSelector(`.card:has-text("${goalName}")`);
    const goalCard = page.locator('.card', { hasText: goalName });
    await expect(goalCard).toBeVisible();

    // 3. Link the portfolio to the goal
    const linkButton = goalCard.getByTestId(`link-asset-button-${goal.id}`);
    await expect(linkButton).toBeEnabled();
    await linkButton.click();
    const assetLinkModal = page.getByRole('dialog');
    await expect(assetLinkModal).toBeVisible();
    await assetLinkModal.getByRole('combobox').selectOption({ label: `${portfolio.name} (Portfolio)` });
    await assetLinkModal.getByRole('button', { name: 'Link' }).click();
    await expect(assetLinkModal).not.toBeVisible();

    // 4. Verify progress
    await page.reload();
    await page.waitForSelector(`.card:has-text("${goalName}")`);
    await goalCard.getByRole('button', { name: 'Show Details' }).click();
    const detailView = goalCard.locator('.bg-gray-100');
    await expect(detailView).toBeVisible();

    // Total value of portfolio is ~1500. Goal target is 2000. Progress should be ~75%.
    await expect(detailView.getByText(/75.00% Complete/)).toBeVisible();
  });
});
