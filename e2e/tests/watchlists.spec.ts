import { test, expect } from '@playwright/test';

test.describe('Watchlists', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByLabel('Email address').fill('test@example.com');
    await page.getByLabel('Password').fill('password');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await page.waitForURL('**/dashboard');
    await page.getByRole('link', { name: 'Watchlists' }).click();
    await page.waitForURL('**/watchlists');
  });

  test('should allow creating, updating, and deleting a watchlist', async ({ page }) => {
    // Create a new watchlist
    await page.getByRole('button', { name: 'Create Watchlist' }).click();
    await page.getByLabel('Watchlist Name').fill('My E2E Watchlist');
    await page.getByRole('button', { name: 'Create' }).click();
    await expect(page.getByRole('combobox')).toHaveValue(/My E2E Watchlist/);

    // Add an asset to the watchlist
    await page.getByRole('button', { name: 'Add Asset' }).click();
    await page.getByPlaceholder('Search for an asset...').fill('AAPL');
    await page.getByText('Apple Inc.').click();
    await page.getByRole('button', { name: 'Add to Watchlist' }).click();

    // Wait for the asset to appear in the table.
    const assetRow = page.locator('tr', { hasText: 'AAPL' });
    await expect(assetRow).toBeVisible();
    await expect(assetRow.getByText('Apple Inc.')).toBeVisible();

    // Remove the asset from the watchlist
    await assetRow.getByRole('button', { name: 'Delete' }).click();
    await expect(page.getByText('Are you sure you want to remove this asset?')).toBeVisible();
    await page.getByRole('button', { name: 'Confirm' }).click();
    await expect(assetRow).not.toBeVisible();


    // Delete the watchlist
    await page.getByRole('button', { name: 'Delete Watchlist' }).click();
    await expect(page.getByText('Are you sure you want to delete this watchlist?')).toBeVisible();
    await page.getByRole('button', { name: 'Confirm' }).click();
    await expect(page.getByText('My E2E Watchlist')).not.toBeVisible();
  });
});
