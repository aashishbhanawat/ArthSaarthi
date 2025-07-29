# Feature Plan: E2E Test Suite Expansion

**Date:** 2025-07-29
**Status:** Completed

## 1. Goal

To expand the existing end-to-end (E2E) test suite to cover all major user-facing features of the application. This will solidify the application's foundation, increase confidence in deployments, and prevent regressions as new features are added.

**Retrospective Note:** The implementation of this plan was successful. However, a significant portion of the effort was dedicated to stabilizing the Docker Compose E2E environment itself, which involved debugging a complex cascade of configuration issues across all services. This foundational work was critical for the success of the test suite.

## 2. Scope

The new E2E tests will cover the following user flows, which are currently only tested manually:

1.  **Portfolio Management (as a standard user):**
    *   Creating a new portfolio.
    *   Viewing a portfolio's detail page.
    *   Deleting a portfolio.
2.  **Transaction Management (as a standard user):**
    *   Adding a BUY transaction for a new asset.
    *   Adding a BUY transaction for an existing asset.
    *   Adding a SELL transaction.
    *   Verifying that a user cannot sell more assets than they own.
3.  **Dashboard Verification (as a standard user):**
    *   Verifying that the dashboard summary cards render with data after transactions are added.
    *   Verifying that the Asset Allocation and Portfolio History charts render with data.

## 3. Implementation Plan

A new test file, `e2e/tests/portfolio-and-dashboard.spec.ts`, will be created to house these new tests.

### a. Test Setup (`beforeAll` / `beforeEach`)

*   The `beforeAll` hook will be responsible for setting up a clean state for the entire test file run. This includes:
    1.  Resetting the database via an API call to `/testing/reset-db`.
    2.  Creating the initial Admin user via the UI.
    3.  Logging in as the Admin user.
    4.  Creating a new Standard User via the User Management UI.
    5.  Logging out.
*   The `beforeEach` hook will log in as the newly created Standard User, ensuring each test starts from the dashboard as an authenticated user.

### b. Test Cases

The following tests will be implemented sequentially:

1.  **`should allow a user to create, view, and delete a portfolio`**: This test will cover the full lifecycle of a portfolio.
2.  **`should allow a user to add various types of transactions`**: This test will verify that BUY and SELL transactions can be added successfully for both new and existing assets.
3.  **`should prevent a user from creating an invalid SELL transaction`**: This test will specifically check the business logic that prevents a user from selling more shares than they hold.
4.  **`should display correct data on the dashboard after transactions`**: This test will add transactions and then navigate to the dashboard to verify that the summary cards and charts update accordingly.