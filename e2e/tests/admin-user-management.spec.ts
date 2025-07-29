import { test, expect, Page } from '@playwright/test';

const testUser = {
  name: 'Test User E2E',
  email: `test.e2e.${Date.now()}@example.com`, // Use unique email to avoid conflicts
  password: 'Password123!',
};

test.describe('Admin User Management Flow', () => {
  let page: Page;

  test.beforeAll(async ({ browser, request }) => {
    // Reset the database before all tests
    const resetResponse = await request.post('/api/v1/testing/reset-db');
    expect(resetResponse.status()).toBe(204);

    // Create a page and perform the initial admin setup once for all tests in this file.
    page = await browser.newPage();
    await page.goto('/');
    await page.getByLabel('Full Name').fill('Admin User');
    await page.getByLabel('Email').fill(process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com');
    await page.getByLabel('Password', { exact: true }).fill(process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!');
    await page.getByRole('button', { name: 'Create Admin Account' }).click();
    await expect(page.getByRole('heading', { name: 'Sign in to your account' })).toBeVisible();

    // Login as Admin
    await page.getByLabel('Email address').fill(process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com');
    await page.getByLabel('Password').fill(process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('link', { name: 'User Management' })).toBeVisible();
  });

  test.afterAll(async () => {
    await page.close();
  });

  test('should allow an admin to create, update, and delete a user', async () => {
    // Navigate to User Management
    await page.getByRole('link', { name: 'User Management' }).click();
    await expect(page.getByRole('heading', { name: 'User Management' })).toBeVisible();

    // CREATE User
    await page.getByRole('button', { name: 'Create New User' }).click();
    await page.getByLabel('Full Name').fill(testUser.name);
    await page.getByLabel('Email').fill(testUser.email);
    await page.getByLabel('Password', { exact: true }).fill(testUser.password);
    await page.getByRole('button', { name: 'Create User' }).click();
    await expect(page.getByRole('cell', { name: testUser.email })).toBeVisible();

    const userRow = page.getByRole('row', { name: new RegExp(testUser.email) });
    await expect(userRow).toBeVisible();

    // UPDATE User
    await userRow.getByRole('button', { name: 'Edit' }).click();
    await page.getByLabel('Full Name').fill(`${testUser.name} (Updated)`);
    await page.getByRole('button', { name: 'Save Changes' }).click();
    // The modal should close, and the user row should still be visible.
    // We can't check for the name update in the table as it's not displayed.
    await expect(page.getByRole('cell', { name: testUser.email })).toBeVisible();

    // DELETE User
    await userRow.getByRole('button', { name: 'Delete' }).click();
    await page.getByRole('button', { name: 'Confirm Delete' }).click();
    await expect(page.getByRole('cell', { name: testUser.email })).not.toBeVisible();
  });
});