import { test, expect } from '@playwright/test';

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
  password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe('Goal Planning Feature', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin before each test
    await page.goto('/');
    await page.getByLabel('Email address').fill(adminUser.email);
    await page.getByLabel('Password').fill(adminUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // Navigate to goals page by clicking the link in the nav bar
    await page.getByRole('link', { name: 'Goals' }).click();
    await expect(page).toHaveURL(/.*\/goals/);
  });

  test('should allow a user to create, view, link, edit, and delete a goal', async ({ page }) => {
    const goalName = `My E2E Goal ${Date.now()}`;
    const updatedGoalName = `My Updated E2E Goal ${Date.now()}`;

    console.log("Navigated to goals page");
    await page.screenshot({ path: 'goals_page.png' });
    await page.waitForSelector('h1:has-text("Your Goals")');
    console.log("Goals page loaded");

    // Create
    await page.getByRole('button', { name: 'Create Goal' }).click();
    await expect(page.getByRole('heading', { name: 'Create New Goal' })).toBeVisible();
    await page.getByLabel('Goal Name').fill(goalName);
    await page.getByLabel('Target Amount').fill('100000');
    await page.getByLabel('Target Date').fill('2030-01-01');
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page.getByText(goalName)).toBeVisible();

    // View
    await page.getByRole('button', { name: 'View' }).click();
    await expect(page.getByRole('heading', { name: goalName })).toBeVisible();

    // Link
    await page.getByRole('button', { name: 'Link Asset/Portfolio' }).click();
    await expect(page.getByRole('heading', { name: `Link Asset or Portfolio to "${goalName}"` })).toBeVisible();
    const modal = page.locator('.modal-box');
    await modal.getByLabel('Search for an asset...').fill('AAPL');
    await modal.getByRole('button', { name: 'Link Asset' }).click();
    await expect(page.getByText('Asset')).toBeVisible();

    // Go back to goals list
    await page.getByRole('button', { name: '← Back to Goals' }).click();

    // Edit
    await page.getByRole('button', { name: 'Edit' }).first().click();
    await expect(page.getByRole('heading', { name: 'Edit Goal' })).toBeVisible();
    await page.getByLabel('Goal Name').fill(updatedGoalName);
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page.getByText(updatedGoalName)).toBeVisible();

    // Delete
    page.on('dialog', dialog => dialog.accept());
    await page.getByRole('button', { name: 'Delete' }).first().click();
    await expect(page.getByText(updatedGoalName)).not.toBeVisible();
  });
});
