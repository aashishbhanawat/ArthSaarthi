/**
 * E2E Test: Screenshot Capture for User Guide
 * 
 * This test navigates through all key screens and captures screenshots
 * for the HTML user guide documentation.
 * 
 * Screenshots are saved to: e2e/screenshots/
 * 
 * USAGE: These tests are SKIPPED by default. To run them:
 *   GENERATE_SCREENSHOTS=true npx playwright test user-guide-screenshots
 */
import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Skip these tests unless GENERATE_SCREENSHOTS=true
const shouldRun = process.env.GENERATE_SCREENSHOTS === 'true';

// Screenshots saved to /app/screenshots in Docker (mounted from ./e2e/screenshots)
const SCREENSHOT_DIR = '/app/screenshots';

const adminUser = {
    email: process.env.FIRST_SUPERUSER_EMAIL || 'admin@example.com',
    password: process.env.FIRST_SUPERUSER_PASSWORD || 'AdminPass123!',
};

const testUser = {
    name: 'Guide User',
    email: `guide.user.${Date.now()}@example.com`,
    password: 'Password123!',
};

// Ensure screenshot directory exists
test.beforeAll(async () => {
    if (!fs.existsSync(SCREENSHOT_DIR)) {
        fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
    }
});

async function screenshot(page: Page, name: string) {
    await page.screenshot({
        path: path.join(SCREENSHOT_DIR, `${name}.png`),
        fullPage: false,
    });
    console.log(`📸 Captured: ${name}.png`);
}

// Skip all tests in this file unless GENERATE_SCREENSHOTS=true
test.describe.serial('User Guide Screenshots', () => {
    // Skip entire suite if GENERATE_SCREENSHOTS is not set
    test.skip(!shouldRun, 'Skipped: Set GENERATE_SCREENSHOTS=true to run');

    let adminToken: string;

    test.beforeAll(async ({ request }) => {
        // Login as admin
        const adminLoginResponse = await request.post('/api/v1/auth/login', {
            form: { username: adminUser.email, password: adminUser.password },
        });
        expect(adminLoginResponse.ok()).toBeTruthy();
        const { access_token } = await adminLoginResponse.json();
        adminToken = access_token;

        // Create test user
        const createUserResponse = await request.post('/api/v1/users/', {
            headers: { Authorization: `Bearer ${adminToken}` },
            data: { ...testUser, is_admin: false },
        });
        expect(createUserResponse.ok()).toBeTruthy();
    });

    test('01 - Login Page', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');
        await screenshot(page, '01_login');
    });

    test('02 - Dashboard', async ({ page }) => {
        // Login
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
        await page.waitForTimeout(1000); // Allow charts to render
        await screenshot(page, '02_dashboard');
    });

    test('03 - Dashboard Privacy Mode', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

        // Toggle privacy mode
        const privacyToggle = page.locator('[aria-label*="privacy"], [title*="privacy"], button:has(svg)').first();
        await privacyToggle.click();
        await page.waitForTimeout(500);
        await screenshot(page, '03_dashboard_privacy');
    });

    test('04 - Portfolios List', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

        await page.getByRole('link', { name: 'Portfolios' }).click();
        await expect(page.getByRole('heading', { name: 'Portfolios' })).toBeVisible();
        await screenshot(page, '04_portfolios');
    });

    test('05 - Create Portfolio & Add Stock Transaction', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

        // Create portfolio
        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByRole('button', { name: 'Create New Portfolio' }).click();
        await page.getByLabel('Name').fill('My Investment Portfolio');
        await screenshot(page, '05a_create_portfolio_modal');
        await page.getByRole('button', { name: 'Create', exact: true }).click();
        await expect(page.getByRole('heading', { name: 'My Investment Portfolio' })).toBeVisible();
        await screenshot(page, '05b_portfolio_detail_empty');

        // Add Stock Transaction
        await page.getByRole('button', { name: 'Add Transaction' }).click();
        await expect(page.getByRole('heading', { name: 'Add Transaction' })).toBeVisible();
        await page.getByLabel('Asset Type').selectOption('Stock');
        await page.getByLabel('Transaction Type').selectOption('BUY');
        await page.getByRole('textbox', { name: 'Asset' }).pressSequentially('RELIANCE');
        const stockItem = page.locator('li:has-text("RELIANCE")');
        await expect(stockItem).toBeVisible();
        await stockItem.click();
        await page.getByLabel('Quantity').fill('50');
        await page.getByLabel('Price per Unit').fill('2500');
        await page.getByLabel('Date').fill('2024-01-15');
        await screenshot(page, '05c_add_stock_modal');
        await page.getByRole('button', { name: 'Save Transaction' }).click();

        // Portfolio with holding
        await page.waitForTimeout(1000);
        await screenshot(page, '05d_portfolio_with_holding');
    });

    test('06 - Fund Transaction Modal', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByText('My Investment Portfolio').click();
        await page.getByRole('button', { name: 'Add Transaction' }).click();
        await page.getByLabel('Asset Type').selectOption('Mutual Fund');
        await page.locator('#transaction_type_mf').selectOption('BUY');

        // Search MF
        const mfInput = page.getByRole('combobox', { name: 'Asset', exact: true });
        await mfInput.fill('HDFC');
        await page.waitForTimeout(1000);
        await screenshot(page, '06_add_mutual_fund_modal');
        await page.getByRole('button', { name: 'Cancel' }).click();
    });

    test('07 - Bond Transaction Modal', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByText('My Investment Portfolio').click();
        await page.getByRole('button', { name: 'Add Transaction' }).click();
        await page.getByLabel('Asset Type').selectOption('Bond');
        await page.waitForTimeout(500);
        await screenshot(page, '07_add_bond_modal');
        await page.getByRole('button', { name: 'Cancel' }).click();
    });

    test('08 - Fixed Deposit Modal', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByText('My Investment Portfolio').click();
        await page.getByRole('button', { name: 'Add Transaction' }).click();
        await page.getByLabel('Asset Type').selectOption('Fixed Deposit');
        await page.waitForTimeout(500);
        await screenshot(page, '08_add_fd_modal');
        await page.getByRole('button', { name: 'Cancel' }).click();
    });

    test('09 - Recurring Deposit Modal', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByText('My Investment Portfolio').click();
        await page.getByRole('button', { name: 'Add Transaction' }).click();
        await page.getByLabel('Asset Type').selectOption('Recurring Deposit');
        await page.waitForTimeout(500);
        await screenshot(page, '09_add_rd_modal');
        await page.getByRole('button', { name: 'Cancel' }).click();
    });

    test('10 - PPF Account Modal', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByText('My Investment Portfolio').click();
        await page.getByRole('button', { name: 'Add Transaction' }).click();
        await page.getByLabel('Asset Type').selectOption('PPF Account');
        await page.waitForTimeout(500);
        await screenshot(page, '10_add_ppf_modal');
        await page.getByRole('button', { name: 'Cancel' }).click();
    });

    test('11 - RSU/ESPP Award Modal', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByText('My Investment Portfolio').click();

        // Open RSU/ESPP modal via dropdown
        await page.getByRole('button', { name: 'Additional actions' }).click();
        await expect(page.getByText('Add ESPP/RSU Award')).toBeVisible();
        await page.getByText('Add ESPP/RSU Award').click();
        await expect(page.getByRole('heading', { name: 'Add ESPP/RSU Award' })).toBeVisible();
        await page.waitForTimeout(500);
        await screenshot(page, '11_add_rsu_espp_modal');
        await page.getByRole('button', { name: 'Cancel' }).click();
    });

    test('12 - Transaction History Page', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'Transactions' }).click();
        await page.waitForTimeout(1000);
        await screenshot(page, '12_transactions_history');
    });

    test('13 - Import Page', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'Import' }).click();
        await page.waitForTimeout(500);
        await screenshot(page, '13_import_page');
    });

    test('14 - Goals Page', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'Goals' }).click();
        await page.waitForTimeout(500);
        await screenshot(page, '14_goals_page');
    });

    test('15 - Watchlists Page', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'Watchlists' }).click();
        await page.waitForTimeout(500);
        await screenshot(page, '15_watchlists_page');
    });

    test('16 - Profile Page', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'Profile' }).click();
        await page.waitForTimeout(500);
        await screenshot(page, '16_profile_page');
    });

    test('17 - Admin User Management', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'User Management' }).click();
        await page.waitForTimeout(500);
        await screenshot(page, '17_admin_users');
    });

    test('18 - Admin Interest Rates', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'Interest Rates' }).click();
        await page.waitForTimeout(500);
        await screenshot(page, '18_admin_interest_rates');
    });

    test('19 - Admin System Maintenance', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'System Maintenance' }).click();
        await page.waitForTimeout(500);
        await screenshot(page, '19_admin_maintenance');
    });

    test('20 - Holding Drill-down', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByText('My Investment Portfolio').click();

        // Click on a holding row to drill down
        const holdingsTable = page.locator('.card', { hasText: 'Holdings' });
        const holdingRow = holdingsTable.getByRole('row', { name: /RELIANCE/ });
        await holdingRow.click();
        await page.waitForTimeout(500);
        await screenshot(page, '20_holding_drilldown');
    });

    // ========== v1.1.0 Features ==========

    test('21 - Dark Theme Toggle', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

        // Click the Dark mode button in the theme selector
        await page.getByRole('button', { name: 'Dark', exact: true }).click();
        await page.waitForTimeout(500);
        await screenshot(page, '21_dark_theme');

        // Reset to light for other tests
        await page.getByRole('button', { name: 'Light', exact: true }).click();
    });

    test('22 - Benchmark Comparison', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'Portfolios' }).click();
        await page.getByText('My Investment Portfolio').click();
        await page.waitForTimeout(1000);

        // Screenshot the portfolio page which may show benchmark info
        await screenshot(page, '22_portfolio_analytics');
    });

    test('23 - Diversification Analysis', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        // Dashboard shows allocation/diversification charts
        await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
        await page.waitForTimeout(1000);
        await screenshot(page, '23_asset_allocation');
    });

    test('24 - Import Formats', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'Import' }).click();
        await page.waitForTimeout(500);
        await screenshot(page, '24_import_formats');
    });

    test('25 - Transaction Filter Types', async ({ page }) => {
        await page.goto('/');
        await page.getByLabel('Email address').fill(adminUser.email);
        await page.getByLabel('Password').fill(adminUser.password);
        await page.getByRole('button', { name: 'Sign in' }).click();

        await page.getByRole('link', { name: 'Transactions' }).click();
        await page.waitForTimeout(500);

        // Click the Type dropdown to show all transaction types
        const typeFilter = page.locator('#type-filter');
        await typeFilter.click();
        await screenshot(page, '25_transaction_type_filter');
    });
});
