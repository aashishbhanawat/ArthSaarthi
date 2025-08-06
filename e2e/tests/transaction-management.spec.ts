import { test, expect, Page } from '@playwright/test';

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
  password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

const portfolioName = 'E2E Transaction Test Portfolio';
const transactionTicker = 'GOOGL';

test.describe('Transaction Management Flow', () => {
  test.beforeEach(async ({ page }) => {
    // 1. Login as Admin
    await page.goto('/');
    await page.getByLabel('Email address').fill(adminUser.email);
    await page.getByLabel('Password').fill(adminUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // 2. Create a portfolio
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Portfolio Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // 3. Add a transaction to it
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    const assetInput = page.getByLabel('Asset');
    // Use pressSequentially for better user simulation and to trigger debounced search
    await assetInput.pressSequentially(transactionTicker);
    // The asset should exist from a previous test, so we select it from the list.
    await page.waitForResponse(response => response.url().includes('/api/v1/assets/lookup'));
    const listItem = page.locator(`li:has-text("${transactionTicker}")`);
    await expect(listItem).toBeVisible();
    await listItem.click();
    await page.getByLabel('Type').selectOption('BUY');
    await page.getByLabel('Quantity').fill('10');
    await page.getByLabel('Price per Unit').fill('150');
    await page.getByLabel('Date').fill('2023-01-15');
    await page.getByRole('button', { name: 'Save Transaction' }).click();
    await expect(page.getByRole('heading', { name: 'Add Transaction' })).not.toBeVisible();
  });

  test('should allow a user to edit and delete a transaction', async ({ page }) => {
    // At this point, we are on the portfolio detail page with one transaction
    await expect(page.getByRole('heading', { name: portfolioName, exact: true })).toBeVisible();

    // Find the transaction row
    const transactionRow = page.locator('tr', { hasText: transactionTicker });
    await expect(transactionRow).toBeVisible();
    await expect(transactionRow.locator('td').nth(3)).toHaveText('10'); // Check initial quantity

    // EDIT the transaction
    await transactionRow.getByRole('button', { name: `Edit transaction for ${transactionTicker}` }).click();
    await expect(page.getByRole('heading', { name: 'Edit Transaction' })).toBeVisible();
    await page.getByLabel('Quantity').fill('25');
    await page.getByRole('button', { name: 'Save Changes' }).click();
    await expect(page.getByRole('heading', { name: 'Edit Transaction' })).not.toBeVisible();
    await expect(transactionRow.locator('td').nth(3)).toHaveText('25');

    // DELETE the transaction
    await transactionRow.getByRole('button', { name: `Delete transaction for ${transactionTicker}` }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.getByRole('button', { name: 'Confirm Delete' }).click();
    await expect(page.getByRole('dialog')).not.toBeVisible();
    await expect(page.getByText(/no transactions found/i)).toBeVisible();
  });
});