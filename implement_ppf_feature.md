# Implementation Prompt: Public Provident Fund (PPF) Tracking (FR4.3.4)

**To:** Jules (AI Assistant)
**From:** Gemini Code Assist
**Date:** 2025-09-08
**Subject:** Implement Full-Stack Public Provident Fund (PPF) Tracking Feature

---

## 1. Objective

Your task is to implement the full-stack "Public Provident Fund (PPF) Tracking" feature as defined in `FR4.3.4_ppf_tracking_v2.md`. This feature requires treating a PPF account as a standard `Asset` and its deposits as `Transaction`s, with a robust backend for automated interest calculation.

Please follow the implementation phases in order, starting with the backend.

---

## 2. Phase 1: Backend Implementation

### 2.1. Database Model & Schema Changes

*   **Update `backend/app/models/asset.py`:**
    *   Add two new nullable columns to the `Asset` model:
        *   `account_number: Mapped[Optional[str]]`
        *   `opening_date: Mapped[Optional[date]]`
*   **Update `backend/app/schemas/asset.py`:**
    *   Add `PPF = "PPF"` to the `AssetType` enum.
    *   Add `account_number: Optional[str] = None` and `opening_date: Optional[date] = None` to the `AssetCreate` schema.
*   **Update `backend/app/schemas/transaction.py`:**
    *   Add `CONTRIBUTION = "CONTRIBUTION"` and `INTEREST_CREDIT = "INTEREST_CREDIT"` to the `TransactionType` enum.
*   **Create `backend/app/models/historical_interest_rate.py`:**
    *   Define a new `HistoricalInterestRate` model with columns: `id` (UUID), `scheme_name` (String), `start_date` (Date), `end_date` (Date), `rate` (Numeric).
*   **Database Migration:**
    *   Due to potential inconsistencies with auto-generation, create the migration script manually.
    *   Run `alembic revision -m "add ppf and interest rate models"` to generate a blank migration file.
    *   Populate the `upgrade()` function to create the `historical_interest_rates` table and add the `account_number` and `opening_date` columns to the `assets` table.
    *   Populate the `downgrade()` function with the corresponding drop operations.

### 2.2. Data Seeding for Interest Rates

*   **Create `backend/app/db/initial_data.py`:**
    *   Create a function `seed_interest_rates(db: Session)` that iterates through `HISTORICAL_PPF_RATES` from `backend/app/db/seed_data/ppf_interest_rates.py`.
    *   For each rate, it should check if a rate for that scheme and start date already exists. If not, it creates a new `HistoricalInterestRate` record.
*   **Update `backend/app/cli.py`:**
    *   In the `init_db` function, after creating tables, call the new `seed_interest_rates(db)` function to populate the historical rates.

### 2.3. CRUD & API Endpoints

*   **Create `backend/app/crud/crud_historical_interest_rate.py`:**
    *   Implement a standard `CRUDBase` for the `HistoricalInterestRate` model.
*   **Create `backend/app/api/v1/endpoints/admin.py`:**
    *   Create a new router for admin-only tasks.
    *   Implement endpoints for full CRUD operations on historical interest rates, protected by the `get_current_admin_user` dependency.
*   **Update `backend/app/api/v1/endpoints/assets.py`:**
    *   Ensure the `create_asset` endpoint correctly handles the new optional `account_number` and `opening_date` fields.
*   **Update `backend/app/api/v1/api.py`:**
    *   Include the new `admin` router.

### 2.4. Business Logic & Valuation

*   **Update `backend/app/crud/crud_holding.py`:**
    *   In `get_portfolio_holdings_and_summary`, add a new section to process PPF assets.
    *   **PPF Calculation Logic (Accurate Monthly Method):**
        1.  Fetch all `CONTRIBUTION` transactions for the PPF asset.
        2.  Iterate through each financial year (April 1st to March 31st) from the PPF `opening_date` to today.
        3.  For each month within that year, determine the minimum balance between the 5th and the end of the month.
        4.  Look up the applicable annual interest rate for that specific month from the `historical_interest_rates` table and calculate the monthly interest on this minimum balance (`applicable_rate / 12`).
        5.  Sum up all 12 monthly interest amounts for the financial year.
        6.  **Crucially, if the financial year is completed, the system must automatically create (or update) a single, read-only `INTEREST_CREDIT` transaction for the total calculated interest, dated March 31st of that financial year.**
        7.  The final `current_balance` is the sum of all `CONTRIBUTION` transactions plus all *saved* `INTEREST_CREDIT` transactions, plus the on-the-fly calculated interest for the *current* financial year.
*   **Recalculation Logic (Smart Recalculation):**
    *   The "smart recalculation" logic must be implemented in the transaction management endpoints (`POST`, `PUT`, `DELETE` in `transactions.py`).
    *   When a `CONTRIBUTION` transaction is modified, the endpoint must determine the financial year of that transaction.
    *   It must then execute a `DELETE` statement to remove all `INTEREST_CREDIT` transactions for that specific PPF asset with a transaction date on or after the start of that financial year.
    *   This invalidates the interest calculations from the point of change onwards. The `get_portfolio_holdings_and_summary` function will then naturally re-calculate and create only the missing interest transactions on the next view, ensuring efficiency.

---

## 3. Phase 2: Frontend Implementation

*   **Update "Add Asset" Flow:**
    *   In `TransactionFormModal.tsx`, add "PPF Account" as an asset type.
    *   When selected, show fields for `Institution Name`, `Account Number`, and `Opening Date`. This will use the existing `createAsset` mutation.
*   **Update "Add Transaction" Flow:**
    *   When a PPF asset is selected, the transaction type should default to `CONTRIBUTION`.
*   **Update Drill-Down View:**
    *   When a user clicks on a PPF holding, the `HoldingDetailModal` should be adapted to show a list of all `CONTRIBUTION` and system-generated `INTEREST_CREDIT` transactions, providing a clear, auditable history.
*   **Create Admin UI:**
    *   Create a new admin page (`/admin/interest-rates`) for managing the historical interest rates.

---

## 4. Phase 3: Testing

*   **Backend:**
    *   Create `backend/app/tests/api/v1/test_ppf_calculations.py`.
    *   Write extensive tests for the interest calculation logic, validating its output against a known-correct spreadsheet calculation for multiple years.
    *   Test the automatic creation, deletion, and recreation of `INTEREST_CREDIT` transactions.
    *   Add tests for the new admin endpoints for managing interest rates.
*   **E2E:**
    *   Create a new E2E test file, `e2e/tests/ppf-tracking.spec.ts`.
    *   The test will:
        1.  Create a PPF account.
        2.  Add several `CONTRIBUTION` transactions across different financial years.
        3.  Verify the calculated `Current Balance` in the holdings table is correct.
        4.  Open the drill-down view and verify that both the `CONTRIBUTION` and the auto-generated `INTEREST_CREDIT` transactions are listed correctly.

---

## 5. Quality & Process Requirements

Adherence to these requirements is mandatory for task completion.

*   **UI Consistency:** The new UI must be visually consistent with the existing application. Please refer to the Dashboard, Portfolios, and Transaction History pages as a reference for styling, layout, and component usage (e.g., cards, buttons, forms).
*   **Code Style & Reuse:** The new code must follow the existing coding style (e.g., `ruff` for backend, `eslint` for frontend). Reuse existing components and utility functions wherever possible to maintain a clean and DRY codebase.
*   **Mandatory Dockerless Testing:** Due to limited disk space in our development environment, you must use the local test runner script for verification. Do not use `docker compose`.
    *   See all options: `./run_local_tests.sh --help`
    *   Run only db migratios: `./run_local_tests.sh migrations --db postgres`
    *   Run only linters: `./run_local_tests.sh lint`
    *   Run only backend tests: `./run_local_tests.sh backend`
    *   Run only frontend tests: `./run_local_tests.sh frontend`
    *   Run only E2E tests: `./run_local_tests.sh e2e`
    *   Run the entire suite: `./run_local_tests.sh all`
*   **Documentation:** As per our project standards, you must update all relevant documentation before finalizing the task as per `COMMIT_TEMPLATE.md`.
*   **Definition of Done:** The task is complete only after all automated tests (including E2E) pass and a manual E2E check confirms the UI is correct.

### How to Debug E2E Tests

If you encounter failures in the E2E tests, use these Playwright debugging tools:

*   **Using the `playwright` object in the Console (Debug Mode):** When Playwright is launched in debug mode (e.g., by setting `PWDEBUG=1`), a special `playwright` object becomes available in the browser's console for inspecting elements.
*   **Trace Viewer:** Playwright's Trace Viewer provides a comprehensive view of test execution, including console output, network requests, and DOM snapshots.

