import { test, expect } from '@playwright/test';

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
  password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

import { login } from '../utils/login';

test.describe.serial('Admin User Management Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin before each test
    await login(page, adminUser.email, adminUser.password);
  });

  test('should allow an admin to create, update, and delete a user', async ({ page }) => {
    const testUser = {
      fullName: 'Test User E2E',
      email: `test.user.${Date.now()}@example.com`,
      password: 'PasswordE2E123!',
    };
    const updatedName = `${testUser.fullName} (Updated)`;

    // Navigate to User Management
    await page.getByRole('link', { name: 'User Management' }).click();
    await expect(page.getByRole('heading', { name: 'User Management' })).toBeVisible();

    // CREATE User
    await page.getByRole('button', { name: 'Create New User' }).click();
    const createModal = page.getByRole('dialog');
    await expect(createModal.getByRole('heading', { name: 'Create New User' })).toBeVisible();
    await createModal.getByLabel('Full Name').fill(testUser.fullName);
    await createModal.getByLabel('Email', { exact: true }).fill(testUser.email);
    await createModal.getByLabel('Password').fill(testUser.password);
    await createModal.getByRole('button', { name: 'Create User' }).click();

    // Verify creation
    await expect(createModal).not.toBeVisible();
    const userRow = page.getByRole('row', { name: new RegExp(testUser.email) });
    await expect(userRow).toBeVisible();

    // UPDATE User
    await userRow.getByRole('button', { name: 'Edit' }).click();
    const editModal = page.getByRole('dialog');
    await expect(editModal.getByRole('heading', { name: 'Edit User' })).toBeVisible();
    await expect(editModal.getByLabel('Full Name')).toHaveValue(testUser.fullName); // Assert original value
    await editModal.getByLabel('Full Name').fill(updatedName);
    await editModal.getByRole('button', { name: 'Save Changes' }).click(); // Save

    // Verify update
    await expect(editModal).not.toBeVisible();
    // Re-open the edit modal to verify the name was persisted correctly
    await userRow.getByRole('button', { name: 'Edit' }).click();
    await expect(editModal.getByLabel('Full Name')).toHaveValue(updatedName);
    await editModal.getByRole('button', { name: 'Cancel' }).click();

    // DELETE User
    await userRow.getByRole('button', { name: 'Delete' }).click();
    const deleteModal = page.getByRole('dialog');
    await expect(deleteModal.getByRole('heading', { name: 'Delete User' })).toBeVisible(); // Corrected heading
    await expect(deleteModal.getByText(`Are you sure you want to delete the user ${testUser.email}?`)).toBeVisible();
    await deleteModal.getByRole('button', { name: 'Confirm Delete' }).click();

    // Verify deletion
    await expect(deleteModal).not.toBeVisible();
    await expect(page.getByRole('row', { name: new RegExp(testUser.email) })).not.toBeVisible();
  });
});

