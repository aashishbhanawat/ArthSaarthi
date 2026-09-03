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
    // 1. Navigate to Income & Tax Hub via navbar link
    await page.getByRole("link", { name: "Income & Tax Hub" }).click();
    await expect(page).toHaveURL(/.*\/income/);

    // Verify heading on Income Tab
    await expect(
      page.getByRole("heading", { name: /Income & TDS Data Management/i }),
    ).toBeVisible({ timeout: 10000 });

    // Verify key summary elements on Income Page
    await expect(page.getByText(/Gross Income/i).first()).toBeVisible();
    await expect(page.getByText(/TDS Credited/i).first()).toBeVisible();

    // 2. Switch to Tax Deductions Tab (Chapter VI-A)
    await page.getByRole("button", { name: "Tax Deductions (Chapter VI-A)" }).click();
    await expect(
      page.getByRole("heading", { name: /Tax Deductions & Chapter VI-A/i }),
    ).toBeVisible({ timeout: 10000 });

    // Verify statutory capping progress meters
    await expect(page.getByText(/Section 80C/i).first()).toBeVisible();
    await expect(page.getByText(/Section 80D/i).first()).toBeVisible();

    // 3. Switch to Consolidated Tax Readiness Summary Tab
    await page.getByRole("button", { name: "Tax Readiness Summary" }).click();
    await expect(
      page.getByRole("heading", { name: /Tax Readiness Summary/i }),
    ).toBeVisible({ timeout: 10000 });

    // Verify non-advisory legal notice banner (FR16.4.1)
    await expect(
      page.getByText(/IMPORTANT LEGAL NOTICE|TAX DISCLAIMER/i).first(),
    ).toBeVisible();

    // Verify Old Regime vs New Regime comparison cards
    await expect(page.getByText(/Old Tax Regime/i).first()).toBeVisible();
    await expect(page.getByText(/New Tax Regime/i).first()).toBeVisible();
  });
});
