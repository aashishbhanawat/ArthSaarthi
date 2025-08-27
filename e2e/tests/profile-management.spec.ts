import { test, expect } from '@playwright/test';

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
  password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

const testUser = {
  fullName: 'Test User E2E',
  email: `test.user.${Date.now()}@example.com`,
  password: 'PasswordE2E123!',
};

test.describe.serial('Profile Management', () => {
    test.beforeAll(async ({ browser }) => {
        const page = await browser.newPage();
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

        // Create a user for the tests
        await page.getByRole('link', { name: 'User Management' }).click();
        await page.getByRole('button', { name: 'Create New User' }).click();
        const createModal = page.getByRole('dialog');
        await createModal.getByLabel('Full Name').fill(testUser.fullName);
        await createModal.getByLabel('Email', { exact: true }).fill(testUser.email);
        await createModal.getByLabel('Password').fill(testUser.password);
        await createModal.getByRole('button', { name: 'Create User' }).click();
        await expect(page.getByRole('row', { name: new RegExp(testUser.email) })).toBeVisible();

        // Logout
        await page.getByRole('button', { name: new RegExp(testUser.fullName) }).click();
        await page.getByRole('menuitem', { name: 'Logout' }).click();
        await expect(page.getByRole('heading', { name: 'Sign in to your account' })).toBeVisible();
        await page.close();
    });

    test('allows a user to update their name and change their password', async ({ page }) => {
        await page.goto('/');
        // 1. Login as the new user
        await page.getByLabel('Email address').fill(testUser.email);
        await page.getByLabel('Password').fill(testUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
        await expect(page.getByRole('button', { name: new RegExp(testUser.fullName) })).toBeVisible();

        // 2. Navigate to profile page
        await page.getByRole('button', { name: new RegExp(testUser.fullName) }).click();
        await page.getByRole('menuitem', { name: 'Profile Settings' }).click();
        await expect(page.getByRole('heading', { name: 'Profile Settings' })).toBeVisible();

        // 3. Update full name
        const updatedName = `${testUser.fullName} (Updated)`;
        await page.getByLabel('Full Name').fill(updatedName);
        await page.getByRole('button', { name: 'Save' }).click();

        // The name in the nav bar should update
        await expect(page.getByRole('button', { name: new RegExp(updatedName) })).toBeVisible();

        // 4. Change password
        const newPassword = 'newPassword456';
        await page.getByLabel('Current Password').fill(testUser.password);
        await page.getByLabel('New Password').fill(newPassword);
        await page.getByLabel('Confirm New Password').fill(newPassword);
        await page.getByRole('button', { name: 'Change Password' }).click();
        await expect(page.getByText('Password updated successfully')).toBeVisible();

        // 5. Logout
        await page.getByRole('button', { name: new RegExp(updatedName) }).click();
        await page.getByRole('menuitem', { name: 'Logout' }).click();
        await expect(page.getByRole('heading', { name: 'Sign in to your account' })).toBeVisible();

        // 6. Login with new password
        await page.getByLabel('Email address').fill(testUser.email);
        await page.getByLabel('Password').fill(newPassword);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
        await expect(page.getByRole('button', { name: new RegExp(updatedName) })).toBeVisible();

        // 7. Logout again
        await page.getByRole('button', { name: new RegExp(updatedName) }).click();
        await page.getByRole('menuitem', { name: 'Logout' }).click();
        await expect(page.getByRole('heading', { name: 'Sign in to your account' })).toBeVisible();

        // 8. Verify login fails with old password
        await page.getByLabel('Email address').fill(testUser.email);
        await page.getByLabel('Password').fill(testUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByText('Incorrect email or password')).toBeVisible();
    });
});
