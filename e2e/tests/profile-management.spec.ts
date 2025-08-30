import { test, expect, request } from '@playwright/test';
import { createUser } from './utils';

const testUser = {
  email: `testuser-${Date.now()}@example.com`,
  fullName: 'Test User',
  password: 'ValidPassword123!',
};

test.describe('User Profile Management', () => {
  test.beforeAll(async () => {
    const requestContext = await request.newContext({
      baseURL: process.env.E2E_BACKEND_URL || 'http://backend:8000',
    });
    // First, log in as admin to get a token that can create users
    const adminLoginResponse = await requestContext.post('/api/v1/auth/login', {
      form: {
        username: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
        password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
      },
    });
    expect(adminLoginResponse.ok()).toBeTruthy();
    const { access_token } = await adminLoginResponse.json();

    // Now create the new user
    const createUserResponse = await requestContext.post('/api/v1/users/', {
      headers: {
        Authorization: `Bearer ${access_token}`,
      },
      data: {
        email: testUser.email,
        password: testUser.password,
        full_name: testUser.fullName,
      },
    });
    expect(createUserResponse.ok()).toBeTruthy();
    await requestContext.dispose();
  });

  test('should allow a user to update their profile and change their password', async ({ page }) => {
    // 1. Login with the created user
    await page.goto('/login');
    await page.getByLabel('Email address').fill(testUser.email);
    await page.getByLabel('Password').fill(testUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page).toHaveURL(/.*\/dashboard/);
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // 2. Navigate to the profile page using the link in the user menu
    await page.locator('div.mt-auto').getByRole('link', { name: 'Profile' }).click();
    await expect(page).toHaveURL(/.*\/profile/);
    await expect(page.getByRole('heading', { name: 'User Profile' })).toBeVisible();

    // 3. Update the user's full name
    const newFullName = 'Updated Test User Name';
    const updateProfileForm = page.locator('div.card:has-text("Update Profile Information")');
    await updateProfileForm.getByLabel('Full Name').fill(newFullName);
    await updateProfileForm.getByRole('button', { name: 'Save Changes' }).click();

    // Assert that the success toast is shown
    await expect(page.locator('text=Profile updated successfully!')).toBeVisible();

    // Assert that the full name in the nav bar is updated
    await expect(page.locator(`text=${newFullName}`)).toBeVisible();

    // 4. Change the password
    const newPassword = 'NewValidPassword456!';
    const changePasswordForm = page.locator('div.card:has-text("Change Password")');
    await changePasswordForm.getByLabel('Current Password').fill(testUser.password);
    await changePasswordForm.getByLabel(/^new password$/i).fill(newPassword);
    await changePasswordForm.getByLabel('Confirm New Password').fill(newPassword);
    await changePasswordForm.getByRole('button', { name: 'Update Password' }).click();

    // Assert that the success toast is shown
    await expect(page.locator('text=Password changed successfully!')).toBeVisible();

    // 5. Logout
    await page.getByRole('button', { name: 'Logout' }).click();
    await expect(page).toHaveURL(/.*\/login/);

    // 6. Login with the new password
    await page.getByLabel('Email address').fill(testUser.email);
    await page.getByLabel('Password').fill(newPassword);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page).toHaveURL(/.*\/dashboard/);
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });
});
