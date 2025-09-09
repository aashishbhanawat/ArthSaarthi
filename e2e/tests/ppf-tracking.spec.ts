import { test, expect, Page } from '@playwright/test';

const standardUser = {
  name: 'PPF User E2E',
  email: `ppf.e2e.${Date.now()}@example.com`,
  password: 'Password123!',
};

const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

async function login(page: Page, email = adminUser.email, password = adminUser.password) {
    await page.goto('/');
    await page.getByLabel('Email address').fill(email);
    await page.getByLabel('Password').fill(password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await page.waitForURL('**/dashboard');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
}

async function openTransactionModal(page: Page) {
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await expect(page.getByRole('heading', { name: 'Add Transaction' })).toBeVisible();
}

test.describe.serial('PPF Account Tracking', () => {
  let portfolioId: string;
  const portfolioName = 'PPF Test Portfolio';

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

    const userLoginResponse = await request.post('/api/v1/auth/login', {
        form: { username: standardUser.email, password: standardUser.password },
    });
    expect(userLoginResponse.ok()).toBeTruthy();
    const { access_token: user_access_token } = await userLoginResponse.json();
    const userAuthHeaders = { Authorization: `Bearer ${user_access_token}` };

    const response = await request.post('/api/v1/portfolios/', {
        headers: userAuthHeaders,
        data: { name: portfolioName, description: 'For PPF E2E tests' },
    });
    expect(response.ok()).toBeTruthy();
    const portfolio = await response.json();
    portfolioId = portfolio.id;
  });

  test.beforeEach(async ({ page }) => {
    await login(page, standardUser.email, standardUser.password);
  });

  test('should create a PPF account, add a contribution, and see the holding', async ({ page }) => {
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.waitForURL('**/portfolios');
    await page.locator('.card', { hasText: portfolioName }).click();
    await page.waitForURL(`**/${portfolioId}`);
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // Create PPF Account
    await openTransactionModal(page);
    await page.selectOption('select#asset_type', 'PPF Account');
    await page.fill('input#ppfInstitutionName', 'Test PPF Bank');
    await page.fill('input#ppfAccountNumber', 'PPF123456789');
    await page.fill('input#ppfOpeningDate', '2022-04-15');
    await page.getByRole('button', { name: 'Save Transaction' }).click();
    await expect(page.locator('div[role="dialog"]')).not.toBeVisible();

    // Add Contribution
    await openTransactionModal(page);
    await page.getByLabel('Asset Type').selectOption('Stock'); // This is a workaround to get the asset search to show
    await page.getByRole('textbox', { name: 'Asset' }).pressSequentially('Test PPF Bank');
    const listItem = page.locator(`li:has-text("Test PPF Bank")`);
    await expect(listItem).toBeVisible();
    await listItem.click();

    await page.getByLabel('Contribution Amount').fill('10000');
    await page.getByLabel('Date').fill('2022-05-20');
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    // Verify Holding
    await page.reload();
    await page.waitForLoadState('networkidle');
    const holdingsTable = page.locator('table');
    const ppfRow = holdingsTable.locator('tr', { hasText: 'Test PPF Bank' });
    await expect(ppfRow).toBeVisible();
    const totalInvestment = 10000;
    const currentBalanceCell = ppfRow.locator('td').nth(4); // Assuming Current Value is 5th column
    const balanceText = await currentBalanceCell.innerText();
    const balanceValue = parseFloat(balanceText.replace(/[₹,]/g, ''));
    expect(balanceValue).toBeGreaterThan(totalInvestment);
  });
});
