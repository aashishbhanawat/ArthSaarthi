import { test, expect } from '@playwright/test';

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
    // Clear auth state to ensure a fresh login for each test
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForLoadState('domcontentloaded');

    // Login
    await page.getByLabel('Email address').fill(standardUser.email);
    await page.getByLabel('Password', { exact: true }).fill(standardUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();

    // Wait for the sidebar navigation to appear (renders immediately after auth, unlike Dashboard content)
    await expect(page.getByRole('link', { name: 'Portfolios' })).toBeVisible();
  });

  test('should display the PPF creation form when no PPF account exists', async ({ page }) => {
    const portfolioName = `My PPF Portfolio ${Date.now()}`;

    // 1. Create a portfolio
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // Wait for the "Add Transaction" button to be ready (confirms portfolio detail page is interactive)
    await expect(page.getByRole('button', { name: 'Add Transaction' })).toBeVisible();

    // 2. Open the "Add Transaction" modal
    await page.getByRole('button', { name: 'Add Transaction' }).click();

    const modal = page.locator('div[role="dialog"]');
    await expect(modal).toBeVisible();

    // 3. Select "PPF Account"
    await modal.getByLabel('Asset Type').selectOption({ label: 'PPF Account' });

    // 4. Wait for the PPF asset loading to complete, then verify the creation form
    await expect(page.getByText('Loading PPF details...')).toBeHidden({ timeout: 10000 });
    await expect(page.getByRole('heading', { name: 'Create Your PPF Account' })).toBeVisible();

    // 5. Fill out the form
    await page.getByLabel('Institution Name').fill('E2E Test PPF Bank');
    await page.getByLabel('Account Number').fill('123456789');
    await page.getByLabel('Opening Date').fill('2022-01-01');
    await page.getByLabel('Contribution Amount').fill('5000');
    await page.getByLabel('Contribution Date').fill('2022-01-10');

    // 6. Submit the form
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    // 7. Verify the modal is closed and a success message is shown
    await expect(modal).not.toBeVisible();
    await expect(page.locator('text=PPF account created successfully')).toBeVisible();
  });

  test('should display the PPF contribution form when a PPF account exists', async ({ page, request }) => {
    const portfolioName = `My Existing PPF Portfolio ${Date.now()}`;

    // Login as the user via API to get a token for API requests
    const userLoginResponse = await request.post('/api/v1/auth/login', {
      form: { username: standardUser.email, password: standardUser.password },
    });
    expect(userLoginResponse.ok()).toBeTruthy();
    const { access_token: userToken } = await userLoginResponse.json();
    const userAuthHeaders = { Authorization: `Bearer ${userToken}` };

    // 1. Create a portfolio via API to be faster
    const createPortfolioResponse = await request.post('/api/v1/portfolios/', {
      headers: userAuthHeaders,
      data: { name: portfolioName, description: 'Test portfolio with existing PPF', currency: 'INR' },
    });
    expect(createPortfolioResponse.ok()).toBeTruthy();
    const portfolio = await createPortfolioResponse.json();
    const portfolioId = portfolio.id;

    // 2. Create a PPF account in that portfolio via API
    const createPpfResponse = await request.post(`/api/v1/ppf-accounts/`, {
      headers: userAuthHeaders,
      data: {
        portfolio_id: portfolioId,
        institution_name: "E2E Test PPF Bank - Existing",
        opening_date: "2022-01-01",
        amount: 5000,
        contribution_date: "2022-01-10"
      }
    });
    expect(createPpfResponse.ok()).toBeTruthy();

    // 3. Navigate to the portfolio page via the UI
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await expect(page.getByRole('heading', { name: 'Portfolios' })).toBeVisible();
    await page.getByRole('link', { name: new RegExp(portfolioName) }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // Wait for the "Add Transaction" button to be ready (confirms portfolio detail page is interactive)
    await expect(page.getByRole('button', { name: 'Add Transaction' })).toBeVisible();

    // 4. Open the "Add Transaction" modal
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    const modal = page.locator('div[role="dialog"]');
    await expect(modal).toBeVisible();

    // 5. Select "PPF Account"
    await modal.getByLabel('Asset Type').selectOption({ label: 'PPF Account' });

    // 6. Wait for PPF asset loading, then verify the contribution form
    await expect(page.getByText('Loading PPF details...')).toBeHidden({ timeout: 10000 });
    await expect(page.getByRole('heading', { name: 'Existing PPF Account' })).toBeVisible();
  });
});
