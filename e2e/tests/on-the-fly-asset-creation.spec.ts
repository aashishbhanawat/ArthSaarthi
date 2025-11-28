import { test, expect } from '@playwright/test';
import { login } from '../utils';

test.describe.serial('On-the-Fly Asset Creation', () => {
    let page;
    let portfolioId;

    test.beforeAll(async ({ browser }) => {
        // Increase timeout for setup
        test.setTimeout(60000);
        const context = await browser.newContext();
        page = await context.newPage();
        await login(page);

        // Create a portfolio to work with
        await page.goto('/#/portfolios');
        await page.getByRole('button', { name: 'Create New Portfolio', exact: true }).click();
        const portfolioName = `OnTheFly Test Portfolio ${Date.now()}`;
        await page.getByLabel('Name').fill(portfolioName);
        await page.getByRole('button', { name: 'Create', exact: true }).click();
        await expect(page.getByRole('heading', { name: portfolioName })).toBeVisible();

        // Extract portfolio ID from URL for later verification
        const url = page.url();
        portfolioId = url.split('/').pop();
    });

    test('should allow creating a new stock asset on the fly from the transaction modal', async () => {
        await page.getByRole('button', { name: 'Add Transaction' }).click();

        const transactionModal = page.locator('.modal-content');
        await expect(transactionModal).toBeVisible();

        // Use the creatable select to add a new asset that doesn't exist
        const newTicker = 'NEWCO.L';
        await page.locator('#asset-search').pressSequentially(newTicker, { delay: 100 });
        await page.locator(`div[role="option"]`, { hasText: `Create new asset "${newTicker}"` }).first().click();

        // Fill the rest of the form
        await transactionModal.locator('input[id="quantity"]').fill('100');
        await transactionModal.locator('input[id="price_per_unit"]').fill('12.50');
        await transactionModal.locator('input[id="transaction_date_standard"]').fill('2023-10-01');

        await transactionModal.getByRole('button', { name: 'Save Transaction' }).click();

        // Verify the modal closes and the new holding appears
        await expect(transactionModal).not.toBeVisible();
        await expect(page.getByRole('cell', { name: newTicker })).toBeVisible();
        await expect(page.getByRole('cell', { name: '100' })).toBeVisible();
    });

    test('should allow creating a new stock asset on the fly from the award modal', async () => {
        // Open the dropdown and click the "Add ESPP/RSU Award" button
        await page.getByRole('button', { name: 'Additional actions' }).click();
        await page.getByRole('menuitem', { name: 'Add ESPP/RSU Award' }).click();


        const awardModal = page.locator('.modal-content');
        await expect(awardModal).toBeVisible();

        // Use the creatable select to add a new asset that doesn't exist
        const newTicker = 'AWARD.L';
        await page.locator('#asset-select').pressSequentially(newTicker, { delay: 100 });
        await page.locator(`div[role="option"]`, { hasText: `Create new asset "${newTicker}"` }).first().click();

        // Fill the rest of the form
        await awardModal.locator('input[id="vest_date"]').fill('2023-11-01');
        await awardModal.locator('input[id="gross_qty_vested"]').fill('50');
        await awardModal.locator('input[id="fmv_at_vest"]').fill('25.00');

        await awardModal.getByRole('button', { name: 'Add Award' }).click();

        // Verify the modal closes and the new holding appears
        await expect(awardModal).not.toBeVisible();
        await expect(page.getByRole('cell', { name: newTicker })).toBeVisible();
        await expect(page.getByRole('cell', { name: '50' })).toBeVisible();
    });
});
