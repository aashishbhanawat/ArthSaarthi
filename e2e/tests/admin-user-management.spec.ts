import { test, expect, Page } from '@playwright/test';
import { faker } from '@faker-js/faker';

test.describe.configure({ mode: 'parallel' });

const testUser = {
  name: 'Test User E2E',
  email: faker.internet.email(),
  password: 'Password123!',
};

const adminUser = {
  email: process.env.VITE_TEST_ADMIN_EMAIL || 'admin@example.com',
  password: process.env.VITE_TEST_ADMIN_PASSWORD || 'AdminPass123!',
};

test.describe('Admin User Management Flow', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    // Login as Admin before each test
    await page.goto('/');
    await page.getByLabel('Email address').fill(adminUser.email);
    await page.getByLabel('Password').fill(adminUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('link', { name: 'User Management' })).toBeVisible();
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('should allow an admin to create, update, and delete a user', async ({ page }) => {
    // Navigate to User Management
    await page.getByRole('link', { name: 'User Management' }).click();
    await expect(page.getByRole('heading', { name: 'User Management' })).toBeVisible();

    // CREATE User
    await page.getByRole('button', { name: 'Create New User' }).click();
    await page.getByLabel('Full Name').fill(testUser.name);
    await page.getByLabel('Email').fill(testUser.email);
    await page.getByLabel('Password', { exact: true }).fill(testUser.password);
    await page.getByRole('button', { name: 'Create User' }).click();

    // Verify creation
    await expect(page.getByRole('row', { name: new RegExp(testUser.email) })).toBeVisible();

    // UPDATE User
    const updatedName = `${testUser.name} (Updated)`;
    // Re-query for the row to ensure we have a fresh reference before clicking
    await page.getByRole('row', { name: new RegExp(testUser.email) }).getByRole('button', { name: 'Edit' }).click();
    await expect(page.getByRole('heading', { name: 'Edit User' })).toBeVisible();
    await page.getByLabel('Full Name').fill(updatedName);
    await page.getByRole('button', { name: 'Save Changes' }).click();
    await page.waitForResponse(response => response.url().includes('/api/v1/users/') && response.request().method() === 'PUT');
    
    // Verify update
    // The name is not in the table, so verify the update by re-opening the edit modal
    await page.getByRole('row', { name: new RegExp(testUser.email) }).getByRole('button', { name: 'Edit' }).click();
    await expect(page.getByRole('heading', { name: 'Edit User' })).toBeVisible();
    await expect(page.getByLabel('Full Name')).toHaveValue(updatedName);
    await page.getByRole('button', { name: 'Cancel' }).click(); // Close the modal to continue

    // DELETE User
    await page.getByRole('row', { name: new RegExp(testUser.email) }).getByRole('button', { name: 'Delete' }).click();
    await page.getByRole('button', { name: 'Confirm Delete' }).click();
    
    // Verify deletion
    await expect(page.getByRole('row', { name: new RegExp(testUser.email) })).not.toBeVisible();
  });
});
