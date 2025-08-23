import { test, expect } from '@playwright/test';

test.describe('Watchlists', () => {
  test.beforeEach(async ({ page }) => {
    // Log in before each test
    await page.goto('/login');
    await page.waitForSelector('input[name="username"]');
    await page.fill('input[name="username"]', 'testuser@example.com');
    await page.fill('input[name="password"]', 'a-secure-password');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('should allow a user to create, update, and delete a watchlist', async ({ page }) => {
    await page.goto('/watchlists');

    // Create
    await page.click('button:has-text("New")');
    await page.fill('input[id="name"]', 'My Test Watchlist');
    await page.click('button:has-text("Create")');
    await expect(page.locator('select[id="watchlist-selector"]')).toHaveText(/My Test Watchlist/);

    // Update
    await page.click('button:has-text("Edit")');
    await page.fill('input[id="name"]', 'My Updated Watchlist');
    await page.click('button:has-text("Save")');
    await expect(page.locator('select[id="watchlist-selector"]')).toHaveText(/My Updated Watchlist/);

    // Delete
    page.on('dialog', dialog => dialog.accept());
    await page.click('button:has-text("Delete")');
    await expect(page.locator('select[id="watchlist-selector"]')).not.toHaveText(/My Updated Watchlist/);
  });

  test('should allow a user to add and remove an asset from a watchlist', async ({ page }) => {
    await page.goto('/watchlists');

    // Create a watchlist first
    await page.click('button:has-text("New")');
    await page.fill('input[id="name"]', 'Asset Test Watchlist');
    await page.click('button:has-text("Create")');

    // Add an asset
    await page.click('button:has-text("Add Asset")');
    await page.fill('input[placeholder="Search for an asset..."]', 'Bitcoin');
    await page.locator('div.p-2:has-text("Bitcoin")').locator('button:has-text("Add")').click();
    await page.click('button:has-text("Done")');
    await expect(page.locator('table')).toContainText('Bitcoin');

    // Remove the asset
    await page.locator('button[color="failure"]').click();
    await expect(page.locator('table')).not.toContainText('Bitcoin');
  });
});
