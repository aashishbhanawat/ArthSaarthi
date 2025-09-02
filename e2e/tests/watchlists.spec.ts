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
    // Wait for the detail view to load. Asserting the heading and the empty-state
    // message are visible is a robust way to ensure the component is ready for interaction.
    await expect(page.getByRole('heading', { name: watchlistName })).toBeVisible();
    await expect(page.getByText('This watchlist is empty.')).toBeVisible();

    // Add item
    await page.getByRole('button', { name: 'Add Asset' }).click();
    // Use a robust, accessibility-based locator to find the modal dialog.
    const modal = page.getByRole('dialog', { name: 'Add Asset to Watchlist' });
    await expect(modal).toBeVisible();
    await modal.getByLabel('Search for an asset').fill('AAPL');
    
    // Wait for the debounced search API call to complete before interacting with the results.
    await page.waitForResponse(resp => resp.url().includes('/api/v1/assets/lookup'));

    // Find the list item containing the asset and click the "Link" button inside it.
    // The snapshot shows the button's accessible name is the asset name itself, not "Link".
    // We target the list item first to ensure we click the button for the correct asset.
    await modal.locator('li', { hasText: 'Apple Inc.' }).getByRole('button', { name: 'Apple Inc. (AAPL)' }).click();

    // After selecting the asset, we must click the main button to add it and close the modal.
    await modal.getByRole('button', { name: 'Add Asset to Watchlist' }).click();

    // Wait for the modal to close before asserting, to give time for the async refetch
    await expect(page.getByRole('heading', { name: 'Add Asset to Watchlist' })).not.toBeVisible();

    await expect(page.getByText('AAPL')).toBeVisible();

    // Remove item
    await page.getByRole('button', { name: 'Remove AAPL' }).click();
    await expect(page.getByText('AAPL')).not.toBeVisible();

    // Cleanup
    page.on('dialog', dialog => dialog.accept());
    await page.getByRole('button', { name: `Delete ${watchlistName}` }).click();
    // After deletion, the detail view should disappear, and the main heading should be visible again.
    await expect(page.getByRole('heading', { name: watchlistName })).not.toBeVisible();
    await expect(page.getByRole('heading', { name: 'My Watchlists' })).toBeVisible();
  });
});
