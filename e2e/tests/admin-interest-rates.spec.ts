import { test, expect } from '@playwright/test';

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
  password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('Admin Interest Rate Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin before each test
    await page.goto('/');
    await page.getByLabel('Email address').fill(adminUser.email);
    await page.getByLabel('Password').fill(adminUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should allow an admin to create, update, and delete an interest rate', async ({ page }) => {
    const testRate = {
      schemeName: `E2E_SCHEME_${Date.now()}`,
      startDate: '2025-01-01',
      endDate: '2025-03-31',
      rate: '5.5',
    };
    const updatedRate = '5.75';

    // Navigate to Interest Rate Management
    await page.getByRole('link', { name: 'Interest Rates' }).click();
    await expect(page.getByRole('heading', { name: 'Interest Rate Management' })).toBeVisible();

    // CREATE Rate
    await page.getByRole('button', { name: 'Add New Rate' }).click();
    const createModal = page.getByRole('dialog');
    await expect(createModal.getByRole('heading', { name: 'Add New Interest Rate' })).toBeVisible();
    await createModal.getByLabel('Scheme Name').fill(testRate.schemeName);
    await createModal.getByLabel('Start Date').fill(testRate.startDate);
    await createModal.getByLabel('End Date (optional)').fill(testRate.endDate);
    await createModal.getByLabel('Interest Rate (%)').fill(testRate.rate);
    await createModal.getByRole('button', { name: 'Create Rate' }).click();

    // Verify creation
    await expect(createModal).not.toBeVisible();
    const rateRow = page.getByRole('row', { name: new RegExp(testRate.schemeName) });
    await expect(rateRow).toBeVisible();
    await expect(rateRow.getByText(`${Number(testRate.rate).toFixed(2)}%`)).toBeVisible();

    // UPDATE Rate
    await rateRow.getByRole('button', { name: /edit/i }).click();
    const editModal = page.getByRole('dialog');
    await expect(editModal.getByRole('heading', { name: 'Edit Interest Rate' })).toBeVisible();
    // Instead of asserting the exact string value, which can have floating point representation issues (e.g. "5.500" vs "5.50"),
    // we parse the input's value and compare it numerically for a more robust test.
    const rateValue = await editModal.getByLabel('Interest Rate (%)').inputValue();
    expect(parseFloat(rateValue)).toBeCloseTo(parseFloat(testRate.rate));
    await editModal.getByLabel('Interest Rate (%)').fill(updatedRate);
    await editModal.getByRole('button', { name: 'Save Changes' }).click();

    // Verify update
    await expect(editModal).not.toBeVisible();
    await expect(rateRow.getByText(`${Number(updatedRate).toFixed(2)}%`)).toBeVisible();

    // DELETE Rate
    await rateRow.getByRole('button', { name: /delete/i }).click();
    const deleteModal = page.getByRole('dialog');
    await expect(deleteModal.getByRole('heading', { name: 'Delete Interest Rate' })).toBeVisible();
    await expect(
      deleteModal.getByText(`Are you sure you want to delete the rate for ${testRate.schemeName}`)
    ).toBeVisible();

    await deleteModal.getByRole('button', { name: 'Confirm Delete' }).click();

    // Verify deletion
    await expect(deleteModal).not.toBeVisible();
    await expect(rateRow).not.toBeVisible();
  });
});