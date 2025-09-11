import { test, expect } from '@playwright/test';
import * as fs from 'fs';

const standardUser = {
  name: 'PPF User E2E',
  email: `ppf.e2e.${Date.now()}@example.com`,
  password: 'Password123!',
};

const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('PPF Modal Verification', () => {
  test.beforeAll(async ({ request }) => {
    const adminLoginResponse = await request.post('/api/v1/auth/login', {
      form: { username: adminUser.email, password: adminUser.password },
    });
    expect(adminLoginResponse.ok()).toBeTruthy();
    const { access_token } = await adminLoginResponse.json();
    const adminAuthHeaders = { Authorization: `Bearer ${access_token}` };

    const standardUserCreateResponse = await request.post('/api/v1/users/', {
      headers: adminAuthHeaders,
      data: { ...standardUser, is_admin: false },
    });
    expect(standardUserCreateResponse.ok()).toBeTruthy();
  });

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByLabel('Email address').fill(standardUser.email);
    await page.getByLabel('Password').fill(standardUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should display the PPF creation form when no PPF account exists', async ({ page }, testInfo) => {
    try {
      const portfolioName = `My PPF Portfolio ${Date.now()}`;

      // 1. Create a portfolio
      await page.getByRole('link', { name: 'Portfolios' }).click();
      await page.getByRole('button', { name: 'Create New Portfolio' }).click();
      await page.getByLabel('Name').fill(portfolioName);
      await page.getByRole('button', { name: 'Create', exact: true }).click();
      await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

      // 2. Open the "Add Transaction" modal
      await page.getByRole('button', { name: 'Add Transaction' }).click();

      const modal = page.locator('div[role="dialog"]');
      await expect(modal).toBeVisible();

      // 3. Select "PPF Account"
      await modal.getByLabel('Asset Type').selectOption({ label: 'PPF Account' });

      // 4. Verify the creation form is visible
      await expect(page.getByRole('heading', { name: 'Create Your PPF Account' })).toBeVisible();

      // 5. Take a screenshot
      await page.screenshot({ path: 'e2e/screenshots/ppf_modal_new_account.png' });

    } catch (error) {
      console.log('Test failed. Reading error context...');
      const errorContextPath = testInfo.outputPath('error-context.md');
      if (fs.existsSync(errorContextPath)) {
        const errorContext = fs.readFileSync(errorContextPath, 'utf-8');
        console.log('--- ERROR CONTEXT ---');
        console.log(errorContext);
        console.log('--- END ERROR CONTEXT ---');
      } else {
        console.log(`Could not find error context file at: ${errorContextPath}`);
      }
      throw error;
    }
  });

  test('should display the PPF contribution form when a PPF account exists', async ({ page, request }) => {
    const portfolioName = `My Existing PPF Portfolio ${Date.now()}`;

    // 1. Create a portfolio via API to be faster
    const createPortfolioResponse = await request.post('/api/v1/portfolios/', {
        data: { name: portfolioName, description: 'Test portfolio with existing PPF', currency: 'INR' },
    });
    expect(createPortfolioResponse.ok()).toBeTruthy();
    const portfolio = await createPortfolioResponse.json();
    const portfolioId = portfolio.id;

    // 2. Create a PPF account in that portfolio via API
    const createPpfResponse = await request.post(`/api/v1/portfolios/${portfolioId}/ppf`, {
        data: {
            institution_name: "E2E Test PPF Bank",
            opening_date: "2022-01-01",
            amount: 5000,
            contribution_date: "2022-01-10"
        }
    });
    expect(createPpfResponse.ok()).toBeTruthy();

    // 3. Navigate to the portfolio page
    await page.goto(`/portfolios/${portfolioId}`);
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // 4. Open the "Add Transaction" modal
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    const modal = page.locator('div[role="dialog"]');
    await expect(modal).toBeVisible();

    // 5. Select "PPF Account"
    await modal.getByLabel('Asset Type').selectOption({ label: 'PPF Account' });

    // 6. Verify the contribution form is visible
    await expect(page.getByRole('heading', { name: 'Existing PPF Account' })).toBeVisible();

    // 7. Take a screenshot
    await page.screenshot({ path: 'e2e/screenshots/ppf_modal_existing_account.png' });
  });
});
