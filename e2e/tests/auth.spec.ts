import { test, expect } from '@playwright/test';

test.describe('Auth', () => {
  test('should allow a user to log in and out', async ({ page }) => {
    // Go to the login page
    await page.goto('/');

    // Fill in the email and password
    await page.getByLabel('Email address').fill('test@example.com');
    await page.getByLabel('Password').fill('password');

    // Click the login button
    await page.getByRole('button', { name: 'Sign in' }).click();

    // Wait for the dashboard to load
    await page.waitForURL('**/dashboard');

    // Check that the user is logged in
    await expect(page.getByText('Dashboard')).toBeVisible();

    // Log out
    await page.getByRole('button', { name: 'Logout' }).click();

    // Check that the user is logged out
    await page.waitForURL('**/auth');
    await expect(page.getByRole('heading', { name: 'Sign in to your account' })).toBeVisible();
  });
});
