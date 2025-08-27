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
    await expect(page.getByRole('heading', { name: 'Goals', level: 1 })).toBeVisible();
  });

  test('should allow a user to create, view, link, edit, and delete a goal', async ({ page }) => {
    const goalName = `My E2E Goal ${Date.now()}`;
    const updatedGoalName = `My Updated E2E Goal ${Date.now()}`;
    const assetToLink = 'AAPL';

    // 1. Create a new goal
    await page.getByRole('button', { name: 'Create Goal' }).click();
    const createModal = page.locator('.modal-content');
    await expect(createModal.getByRole('heading', { name: 'Create New Goal' })).toBeVisible();
    await createModal.getByLabel('Goal Name').fill(goalName);
    await createModal.getByLabel('Target Amount').fill('100000');
    await createModal.getByLabel('Target Date').fill('2030-01-01');
    await createModal.getByRole('button', { name: 'Save' }).click();

    // Verify the new goal is in the list
    const goalInList = page.locator(`li:has-text("${goalName}")`);
    await expect(goalInList).toBeVisible();

    // 2. Navigate to detail page and view the goal
    await goalInList.getByRole('link').click();
    await expect(page).toHaveURL(/.*\/goals\/.*/);
    await expect(page.getByRole('heading', { name: goalName, level: 1 })).toBeVisible();

    // 3. Link an asset
    await page.getByRole('button', { name: 'Link Item' }).click();
    const linkModal = page.locator('.modal-content');
    await expect(linkModal).toBeVisible();
    await linkModal.getByLabel('Search Assets').fill(assetToLink);
    await expect(linkModal.locator(`div:has-text("${assetToLink}")`)).toBeVisible();
    await linkModal.getByRole('button', { name: 'Link' }).first().click();

    // Verify the asset is linked on the detail page
    const linkedItemsCard = page.locator('.card', { hasText: 'Linked Items' });
    await expect(linkedItemsCard.getByText(assetToLink)).toBeVisible();

    // 4. Edit the goal
    await page.getByRole('button', { name: 'Edit' }).click();
    const editModal = page.locator('.modal-content');
    await expect(editModal.getByRole('heading', { name: 'Edit Goal' })).toBeVisible();
    await editModal.getByLabel('Goal Name').fill(updatedGoalName);
    await editModal.getByRole('button', { name: 'Save' }).click();

    // Verify the name has been updated on the detail page
    await expect(page.getByRole('heading', { name: updatedGoalName, level: 1 })).toBeVisible();

    // 5. Navigate back to the list and delete the goal
    await page.getByRole('link', { name: '← Back to Goals' }).click();
    await expect(page.getByRole('heading', { name: 'Goals' })).toBeVisible();

    const updatedGoalInList = page.locator(`li:has-text("${updatedGoalName}")`);
    await expect(updatedGoalInList).toBeVisible();

    // Set up listener for the confirmation dialog BEFORE clicking delete
    page.on('dialog', dialog => dialog.accept());

    await updatedGoalInList.getByRole('button', { name: '' }).locator('svg').click(); // Clicks the trash icon

    // Verify the goal is no longer in the list
    await expect(updatedGoalInList).not.toBeVisible();
  });
});
