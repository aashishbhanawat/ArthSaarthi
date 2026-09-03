import { test, expect } from "@playwright/test";

const adminUser = {
  email: process.env.FIRST_SUPERUSER_EMAIL || "admin@example.com",
  password: process.env.FIRST_SUPERUSER_PASSWORD || "AdminPass123!",
};

test.describe("Tax Readiness & Financial Picture Workflow (Release v1.4.0)", () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin before each test
    await page.goto("/");
    await page.getByLabel("Email address").fill(adminUser.email);
    await page.getByLabel("Password", { exact: true }).fill(adminUser.password);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(
      page.getByRole("heading", { name: "Dashboard" }),
    ).toBeVisible();
  });

  test("should navigate through Income, Deductions, and Tax Summary dashboards", async ({
    page,
  }) => {
    // 1. Navigate to Income Data Management Page
    await page.goto("/income");
    await expect(
      page.getByRole("heading", { name: /Income & TDS Data Management|Income Data Management|Income Sources/i }),
    ).toBeVisible({ timeout: 10000 });

    // Verify key summary elements on Income Page
    await expect(page.getByText(/Total Gross Income|Gross Income/i).first()).toBeVisible();
    await expect(page.getByText(/Total TDS Credit|TDS Credited|TDS Deducted/i).first()).toBeVisible();

    // 2. Navigate to Tax Deductions Page (Chapter VI-A)
    await page.goto("/deductions");
    await expect(
      page.getByRole("heading", { name: /Tax Deductions|Chapter VI-A/i }),
    ).toBeVisible({ timeout: 10000 });

    // Verify statutory capping progress meters
    await expect(page.getByText(/Section 80C/i)).toBeVisible();
    await expect(page.getByText(/Section 80D/i)).toBeVisible();

    // 3. Navigate to Consolidated Tax Summary Dashboard
    await page.goto("/tax-summary");
    await expect(
      page.getByRole("heading", { name: /Tax Readiness Summary|Tax Profile/i }),
    ).toBeVisible({ timeout: 10000 });

    // Verify non-advisory legal notice banner (FR16.4.1)
    await expect(
      page.getByText(/informational purposes only|does not constitute financial or tax advice/i),
    ).toBeVisible();

    // Verify Old Regime vs New Regime comparison cards
    await expect(page.getByText(/Old Tax Regime/i)).toBeVisible();
    await expect(page.getByText(/New Tax Regime/i)).toBeVisible();
  });
});
