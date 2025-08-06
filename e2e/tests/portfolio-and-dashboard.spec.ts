import { test, expect, Page } from '@playwright/test';

const standardUser = {
  name: 'Standard User E2E',
  email: `standard.e2e.${Date.now()}@example.com`,
  password: 'Password123!',
};

const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

test.describe.serial('Portfolio and Dashboard E2E Flow', () => {
  test.beforeAll(async ({ request }) => {
    // The global setup has already created the admin user.
    // We just need to log in as admin to create our test-specific standard user.
    const adminLoginResponse = await request.post('/api/v1/auth/login', {
      form: { username: adminUser.email, password: adminUser.password },
    });
    expect(adminLoginResponse.ok()).toBeTruthy();
    const { access_token } = await adminLoginResponse.json();
    const adminAuthHeaders = { Authorization: `Bearer ${access_token}` };

    // Create Standard User via API (as Admin)
    const standardUserCreateResponse = await request.post('/api/v1/users/', {
      headers: adminAuthHeaders,
      data: { ...standardUser, is_admin: false },
    });
    expect(standardUserCreateResponse.ok()).toBeTruthy();
  });

  test.beforeEach(async ({ page }) => {
    // Login as the standard user before each test
    await page.goto('/');
    await page.getByLabel('Email address').fill(standardUser.email);
    await page.getByLabel('Password').fill(standardUser.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should allow a user to create, view, and delete a portfolio', async ({ page }) => {
    const portfolioName = `My E2E Portfolio ${Date.now()}`;

    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();

    // Verify creation and navigation to detail page
    try {
      await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible({ timeout: 5000 });
    } catch (error) {
      console.error(`\n--- E2E DEBUG ---`);
      console.error(`Failed to find heading: "${portfolioName}"`);
      console.error(`Current URL: ${page.url()}`);
      console.error('Dumping page content:\n' + await page.content());
      throw error;
    }

    // Go back and delete
    await page.getByRole('link', { name: 'Back to Portfolios' }).click();

    const portfolioRow = page.locator('.card', { hasText: new RegExp(portfolioName) });
    await expect(portfolioRow).toBeVisible();
    await portfolioRow.getByRole('button', { name: 'Delete' }).click();

    await expect(page.getByRole('dialog')).toBeVisible(); // Verify the modal is open
    // Scope the search to the dialog to click the correct "Delete" button
    await page.getByRole('dialog').getByRole('button', { name: 'Delete' }).click();

    // Verify deletion
    await expect(page.getByRole('heading', { name: 'Portfolios' })).toBeVisible();
    await expect(portfolioRow).not.toBeVisible();
  });

  test('should allow a user to add various types of transactions', async ({ page }) => {
    const portfolioName = `My Transaction Portfolio ${Date.now()}`;
    const newAssetName = 'GOOGL';

    // 1. Create a portfolio to hold transactions
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // 2. Add a BUY transaction for a NEW asset
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Type', { exact: true }).selectOption('BUY');
    await page.getByLabel('Asset').pressSequentially(newAssetName);
    const createAssetButton = page.getByRole('button', { name: `Create Asset "${newAssetName}"` });
    await expect(createAssetButton).toBeVisible();
    await createAssetButton.click();
    await expect(createAssetButton).not.toBeVisible();
    await page.getByLabel('Quantity').fill('10');
    await page.getByLabel('Price per Unit').fill('150.00');
    await page.getByLabel('Date').fill(new Date().toISOString().split('T')[0]);
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    // Verify the new transaction is in the list
    await expect(page.getByRole('row', { name: /GOOGL.*BUY.*10/ })).toBeVisible();

    // 3. Add a SELL transaction for the same asset
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Type', { exact: true }).selectOption('SELL');
    // Use pressSequentially to simulate user typing and avoid race conditions with debounced search
    await page.getByLabel('Asset').pressSequentially(newAssetName);

    // Wait for the debounced search API call to complete before interacting with the results
    await page.waitForResponse(response => response.url().includes('/api/v1/assets/lookup'));

    // Use a direct locator strategy that is more robust for this component.
    const listItem = page.locator(`li:has-text("${newAssetName}")`);
    // Wait for the search result to appear and then press Enter to select it. This is more stable than clicking.
    await expect(listItem).toBeVisible(); // Ensure the item is there
    await listItem.click(); // Click the item directly to ensure selection

    await page.getByLabel('Quantity').fill('5');
    await page.getByLabel('Price per Unit').fill('160.00');
    await page.getByLabel('Date').fill(new Date().toISOString().split('T')[0]);
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    // Verify the SELL transaction is also in the list
    await expect(page.getByRole('row', { name: /GOOGL.*SELL.*5/ })).toBeVisible();
  });

  test('should prevent a user from creating an invalid SELL transaction', async ({ page }) => {
    const portfolioName = `Invalid Sell Portfolio ${Date.now()}`;
    const assetName = 'AAPL'; // Use a different asset to avoid test contamination

    // 1. Create a portfolio
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // 2. Add a BUY transaction for 10 shares
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Type', { exact: true }).selectOption('BUY');
    await page.getByLabel('Asset').pressSequentially(assetName);
    // Handle asset creation since it does not exist in the mock service
    const createAssetButton = page.getByRole('button', { name: `Create Asset "${assetName}"` });
    await expect(createAssetButton).toBeVisible();
    await createAssetButton.click();
    await page.getByLabel('Quantity').fill('10');
    await page.getByLabel('Price per Unit').fill('175.00');
    await page.getByLabel('Date').fill('2023-01-15'); // Use a fixed past date
    await page.getByRole('button', { name: 'Save Transaction' }).click();
    await expect(page.getByRole('row', { name: /AAPL.*BUY.*10/ })).toBeVisible();

    // 3. Attempt to SELL 20 shares (which is more than owned)
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Type', { exact: true }).selectOption('SELL');
    await page.getByLabel('Asset').pressSequentially(assetName);
    await page.waitForResponse(response => response.url().includes('/api/v1/assets/lookup'));
    const listItemSell = page.locator(`li:has-text("${assetName}")`);
    await expect(listItemSell).toBeVisible();
    await listItemSell.click();
    await page.getByLabel('Quantity').fill('20'); // Invalid quantity
    await page.getByLabel('Price per Unit').fill('180.00');
    await page.getByLabel('Date').fill('2023-01-20'); // A date after the buy
    await page.getByRole('button', { name: 'Save Transaction' }).click();

    // 4. Verify the backend error is displayed in the modal
    await expect(page.locator('.alert-error')).toBeVisible();
    await expect(page.locator('.alert-error')).toContainText('Insufficient holdings to sell');

    // 5. Verify the modal is still open and the invalid transaction was not added
    await expect(page.getByRole('heading', { name: 'Add Transaction' })).toBeVisible();
    await page.getByRole('button', { name: 'Cancel' }).click();
    await expect(page.getByRole('row', { name: /AAPL.*SELL.*20/ })).not.toBeVisible();
  });

  test('should display correct data on the dashboard after transactions', async ({ page }) => {
    const portfolioName = `Dashboard Test Portfolio ${Date.now()}`;

    // 1. Create a portfolio
    await page.getByRole('link', { name: 'Portfolios' }).click();
    await page.getByRole('button', { name: 'Create New Portfolio' }).click();
    await page.getByLabel('Name').fill(portfolioName);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

    // 2. Add two different assets
    // Asset 1: 10 GOOGL @ $150
    await page.getByRole('button', { name: 'Add Transaction' }).click();
    await page.getByLabel('Asset').pressSequentially('GOOGL'); // Asset already exists from a previous test
    // Wait for the lookup and select the existing asset from the list
    await page.waitForResponse(response => response.url().includes('/api/v1/assets/lookup'));
    const listItem = page.locator(`li:has-text("GOOGL")`);
    await listItem.click();
    await page.getByLabel('Quantity').fill('10');
    await page.getByLabel('Price per Unit').fill('150');
    await page.getByLabel('Date').fill('2023-02-01');
    await page.getByRole('button', { name: 'Save Transaction' }).click();
    await expect(page.getByRole('row', { name: /GOOGL.*BUY.*10/ })).toBeVisible();

    // 3. Navigate to Dashboard and verify data
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // Verify Total Value. Use a regex to check for a valid currency format,
    // as the exact value will change based on the live market price.
    const totalValueCard = page.locator('.card', { hasText: 'Total Value' });
    await expect(totalValueCard).toContainText(/₹[0-9,]+\.\d{2}/);
  });
});
