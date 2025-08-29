import { test, expect } from '@playwright/test';

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
  password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('Profile Management', () => {
    test('allows a user to update their name and change their password', async ({ page }) => {
        // 1. Login as admin
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
        await expect(page.getByText('Admin User')).toBeVisible();

        // 2. Navigate to profile page
        await page.getByText('Admin User').click();
        await page.getByRole('menuitem', { name: 'Profile Settings' }).click();
        await expect(page.getByRole('heading', { name: 'Profile Settings' })).toBeVisible();

        // 3. Update full name
        const updatedName = 'Admin User (Updated)';
        await page.getByLabel('Full Name').fill(updatedName);
        await page.getByRole('button', { name: 'Save' }).click();

        // The name in the nav bar should update
        await expect(page.getByText(updatedName)).toBeVisible();

        // 4. Change password
        const newPassword = 'newPassword456!';
        await page.getByLabel('Current Password').fill(adminUser.password);
        await page.locator('#new-password').fill(newPassword);
        await page.locator('#confirm-password').fill(newPassword);
        await page.getByRole('button', { name: 'Change Password' }).click();
        await expect(page.getByText('Password updated successfully!')).toBeVisible();

        // 5. Logout
        await page.getByText(updatedName).click();
        await page.getByRole('menuitem', { name: 'Logout' }).click();
        await expect(page.getByRole('heading', { name: 'Sign in to your account' })).toBeVisible();

        // 6. Login with new password
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(newPassword);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
        await expect(page.getByText(updatedName)).toBeVisible();

        // 7. Change password back to original
        await page.getByText(updatedName).click();
        await page.getByRole('menuitem', { name: 'Profile Settings' }).click();
        await page.getByLabel('Current Password').fill(newPassword);
        await page.locator('#new-password').fill(adminUser.password);
        await page.locator('#confirm-password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Change Password' }).click();
        await expect(page.getByText('Password updated successfully!')).toBeVisible();

        // 8. Logout again
        await page.getByText(updatedName).click();
        await page.getByRole('menuitem', { name: 'Logout' }).click();
        await expect(page.getByRole('heading', { name: 'Sign in to your account' })).toBeVisible();

        // 9. Verify login fails with new password
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(newPassword);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByText('Incorrect email or password')).toBeVisible();
    });
});
