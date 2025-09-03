import { test, expect } from '@playwright/test';
import { login } from '../utils';

test.describe('Privacy Mode E2E Test', () => {
  test.beforeEach(async ({ page }) => {
    // Ensure local storage is clean before each test run
    await page.context().clearCookies();
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
    await login(page);
    await page.goto('/dashboard');
    // After login, clear privacy mode specifically to ensure a clean slate for each test
    await page.evaluate(() => localStorage.removeItem('privacyMode'));
    await page.reload();
  });

  test('should selectively hide sensitive data and persist the state', async ({ page }) => {
    const privacyToggleShow = page.getByRole('button', { name: /hide sensitive data/i });
    const privacyToggleHide = page.getByRole('button', { name: /show sensitive data/i });

    // --- Locators ---
    const totalValueCard = page.locator('.card', { hasText: 'Total Value' });
    const sensitiveSummaryValue = totalValueCard.locator('p').last();

    const topMoversTable = page.locator('table:has-text("Top Movers")');
    const nonSensitivePriceValue = topMoversTable.locator('tbody >> tr').first().locator('td').nth(1);

    // --- Regexes ---
    const visibleValueRegex = /^-?₹[0-9,]+\.\d{2}$/;
    const obscuredValue = '₹**,***.**';

    // 1. VERIFY INITIAL STATE (everything visible)
    await expect(sensitiveSummaryValue).toHaveText(visibleValueRegex);
    await expect(nonSensitivePriceValue).toHaveText(visibleValueRegex);

    // 2. TOGGLE PRIVACY MODE ON
    await privacyToggleShow.click();

    // 3. VERIFY SELECTIVE OBSCURING
    // Sensitive value should be hidden
    await expect(sensitiveSummaryValue).toHaveText(obscuredValue);
    // Non-sensitive value should still be visible
    await expect(nonSensitivePriceValue).toHaveText(visibleValueRegex);

    // 4. RELOAD AND VERIFY PERSISTENCE
    await page.reload();
    await page.waitForSelector('.card:has-text("Total Value")'); // Ensure card is visible
    // Sensitive value should still be hidden
    await expect(sensitiveSummaryValue).toHaveText(obscuredValue);
    // Non-sensitive value should still be visible
    await expect(nonSensitivePriceValue).toHaveText(visibleValueRegex);

    // 5. TOGGLE PRIVACY MODE OFF
    await privacyToggleHide.click();

    // 6. VERIFY VALUES ARE VISIBLE AGAIN
    await expect(sensitiveSummaryValue).toHaveText(visibleValueRegex);
    await expect(nonSensitivePriceValue).toHaveText(visibleValueRegex);
  });
});
