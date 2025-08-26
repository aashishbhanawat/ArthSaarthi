import { test, expect } from '@playwright/test';

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
  password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe('Watchlists Feature', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin before each test
    await page.goto('/');
    await page.getByLabel('Email address').fill(adminUser.email);
    await page.getByLabel('Password').fill(adminUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // Navigate to watchlists page by clicking the link in the nav bar
    await page.getByRole('link', { name: 'Watchlists' }).click();
    await expect(page).toHaveURL(/.*\/watchlists/);
  });

  test('should allow a user to create, rename, and delete a watchlist', async ({ page }) => {
    const watchlistName = `My E2E Watchlist ${Date.now()}`;
    const renamedWatchlistName = `My Renamed E2E Watchlist ${Date.now()}`;

    // Wait for the initial loading to complete.
    await expect(page.getByRole('heading', { name: 'My Watchlists' })).toBeVisible({ timeout: 10000 });

    // Create
    await page.getByRole('button', { name: 'Add new watchlist' }).click();
    await expect(page.getByRole('heading', { name: 'Create New Watchlist' })).toBeVisible();
    await page.getByLabel('Watchlist Name').fill(watchlistName);
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page.getByText(watchlistName)).toBeVisible();

    // Rename
    await page.getByRole('button', { name: `Edit ${watchlistName}` }).click();
    await expect(page.getByRole('heading', { name: 'Rename Watchlist' })).toBeVisible();
    await page.getByLabel('Watchlist Name').fill(renamedWatchlistName);
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page.getByText(renamedWatchlistName)).toBeVisible();

    // Delete
    page.on('dialog', dialog => dialog.accept());
    await page.getByRole('button', { name: `Delete ${renamedWatchlistName}` }).click();
    await expect(page.getByText(renamedWatchlistName)).not.toBeVisible();
  });

  test('should allow a user to add and remove items from a watchlist', async ({ page }) => {
    const watchlistName = `My E2E Watchlist For Items ${Date.now()}`;

    // Wait for the initial loading to complete.
    await expect(page.getByRole('heading', { name: 'My Watchlists' })).toBeVisible({ timeout: 10000 });

    // Create a watchlist to work with
    await page.getByRole('button', { name: 'Add new watchlist' }).click();
    await expect(page.getByRole('heading', { name: 'Create New Watchlist' })).toBeVisible();
    await page.getByLabel('Watchlist Name').fill(watchlistName);
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page.getByText(watchlistName)).toBeVisible();

    // Select the newly created watchlist to view its table
    await page.getByText(watchlistName).click();

    // Add item
    await page.getByRole('button', { name: 'Add Asset' }).click();
    await expect(page.getByRole('heading', { name: 'Add Asset to Watchlist' })).toBeVisible();
    await page.getByLabel('Search for an asset').fill('AAPL');
    await page.getByRole('button', { name: 'Apple Inc.' }).click();
    await page.getByRole('button', { name: 'Add Asset to Watchlist' }).click();

    console.log(await page.content());
    await expect(page.getByRole('cell', { name: 'AAPL', exact: true })).toBeVisible();

    // Remove item
    await page.getByRole('button', { name: 'Remove Apple Inc. from watchlist' }).click();
    await expect(page.getByRole('cell', { name: 'AAPL', exact: true })).not.toBeVisible();

    // Cleanup
    page.on('dialog', dialog => dialog.accept());
    await page.getByRole('button', { name: `Delete ${watchlistName}` }).click();
    await expect(page.getByText(watchlistName)).not.toBeVisible();
  });
});
