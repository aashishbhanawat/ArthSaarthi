import { test, expect } from '@playwright/test';

test.describe('User Profile Management', () => {
  const newFullName = 'Updated Test User';
  const newPassword = 'NewPassword123!';

  test('allows a user to update their name and password', async ({ page }) => {
    // 1. Login
    await page.goto('/');
    await page.getByLabel('Email address').fill('admin@example.com');
    await page.getByLabel('Password').fill('AdminPass123!');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    const userDisplay = page.locator('.truncate[title="admin@example.com"]');
    await expect(userDisplay).toContainText('Admin User');

    // 2. Navigate to Profile page
    await page.getByRole('link', { name: 'Profile' }).click();
    await expect(page.getByRole('heading', { name: 'User Profile' })).toBeVisible();

    // 3. Update Profile Information
    const nameInput = page.locator('input#fullName');
    await expect(nameInput).toHaveValue('Admin User');
    await nameInput.fill(newFullName);
    await page.getByRole('button', { name: 'Save Changes' }).click();

    // Verify name is updated in the user display area
    await expect(userDisplay).toContainText(newFullName);

    // 4. Change Password
    await page.getByLabel('Current Password').fill('AdminPass123!');
    await page.getByLabel('New Password').fill(newPassword);
    await page.getByLabel('Confirm New Password').fill(newPassword);
    await page.getByRole('button', { name: 'Update Password' }).click();

    // Check for success message
    await expect(page.getByText('Password updated successfully!')).toBeVisible();

    // 5. Logout
    await page.getByRole('button', { name: 'Logout' }).click();
    await expect(page.getByRole('heading', { name: 'Sign in to your account' })).toBeVisible();

    // 6. Login with new password
    await page.getByLabel('Email address').fill('admin@example.com');
    await page.getByLabel('Password').fill(newPassword);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // Verify the name is still the updated one
    await expect(userDisplay).toContainText(newFullName);
  });
});
