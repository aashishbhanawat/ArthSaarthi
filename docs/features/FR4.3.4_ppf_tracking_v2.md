# Feature Plan: Public Provident Fund (PPF) Tracking

**Status: 🚧 In Progress**
---
**Feature ID:** FR4.3.4
**Title:** Implement Public Provident Fund (PPF) Tracking with Automated Interest Calculation
**User Story:** As a user, I want to track my PPF account with automated interest calculations based on official rates, so I can see its true growth without manual updates and have confidence in the data.

---

## 1. Implementation Progress

*   [x] **Phase 1: Database Schema & Seeding:** The necessary database models, schemas, and migration scripts have been implemented and tested. The database is now ready to store PPF accounts, contributions, and historical interest rates.
*   [x] **Phase 2: Backend Business Logic:** The core valuation logic (`_process_ppf_holdings`) and the "Smart Recalculation" logic for handling contribution updates have been fully implemented and stabilized.
*   [x] **Phase 3: Frontend UI:** The basic UI for adding PPF accounts and contributions is complete. The dedicated drill-down modal for PPF holdings is now implemented.
*   [x] **Phase 4: Testing:** Backend unit tests have been implemented and are passing. The E2E test for the full user flow is also passing.
*   [ ] **Phase 5: Admin UI for Interest Rates:** Implement the admin-only UI for managing historical interest rates.

---

## 2. Objective

The initial MVP for PPF tracking relied on a user-managed `current_balance`, which is inaccurate and cumbersome. This plan details a full implementation of proper contribution tracking and automated, rule-based interest calculations. The core principle is to treat a PPF account as a standard `Asset` and contributions as `Transaction`s, ensuring they appear in the user's main transaction history for full visibility.

---

## 3. UI/UX Requirements & Detailed Mockups

*   **Sectioned View:** PPF accounts will be displayed within the new "Government Schemes" collapsible section in the main holdings table.
*   **Holdings Table Columns:** The "Government Schemes" section will have columns relevant to PPF: Asset (e.g., "PPF Account"), Institution, Opening Date, Current Balance.
*   **User Interactions:**
    *   **Add PPF Account & Contribution:** The "Add Transaction" button opens a modal. When "PPF Account" is selected as the asset type, the UI intelligently adapts based on whether a PPF account already exists for the user.
    *   **Drill-Down View:** Clicking a PPF holding in the main table will open a detailed "passbook" view.
    *   **Interest Rate Management (Admin):** A new UI in the "Admin Settings" area will allow an administrator to view and manage the historical PPF interest rates used in calculations.

### 3.1. Mockup: Add Transaction Modal

This modal has two states.

**State 1: No Existing PPF Account**
The user is guided to create the account and log their first contribution in a single step.

```text
┌──────────────────────────────────────────────────────────┐
│ Add Transaction                                       [X]│
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Asset Type: [ PPF Account ▼ ]                           │
│                                                          │
│  ┌─ Create Your PPF Account ───────────────────────────┐  │
│  │                                                      │  │
│  │  Institution Name (e.g., SBI, HDFC)                  │  │
│  │  [ State Bank of India             ]                │  │
│  │                                                      │  │
│  │  Account Number (Optional)      Opening Date        │  │
│  │  [ 1234567890123456 ]           [ 2023-01-01 ]      │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─ Add First Contribution ─────────────────────────────┐  │
│  │                                                      │  │
│  │  Contribution Amount (₹)        Contribution Date   │  │
│  │  [ 100000.00        ]           [ 2023-01-15 ]      │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                          │
│                                     [ Cancel ] [ Save ]  │
└──────────────────────────────────────────────────────────┘
```

**State 2: Existing PPF Account**
The UI recognizes the existing account, displays its details as read-only, and only prompts for a new contribution.

```text
┌──────────────────────────────────────────────────────────┐
│ Add Transaction                                       [X]│
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Asset Type: [ PPF Account ▼ ]                           │
│                                                          │
│  ┌─ Existing PPF Account ──────────────────────────────┐  │
│  │                                                      │  │
│  │  Institution: State Bank of India                   │  │
│  │  Account #:   1234567890123456                       │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─ Add New Contribution ──────────────────────────────┐  │
│  │                                                      │  │
│  │  Contribution Amount (₹)        Contribution Date   │  │
│  │  [ 5000.00          ]           [ 2024-05-10 ]      │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                          │
│                                     [ Cancel ] [ Save ]  │
└──────────────────────────────────────────────────────────┘
```

### 3.2. Mockup: Holdings Table View

The PPF account will appear in its own collapsible section.

```text
▼ Government Schemes (1)
┌──────────────────────────────────────────────────────────────────────────┐
│ Asset       | Institution          | Opening Date      | Current Balance │
├─────────────┼──────────────────────┼───────────────────┼─────────────────┤
│ PPF Account | State Bank of India  | 01 Jan 2023       | ₹1,16,740.09    │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.3. Mockup: PPF Drill-Down "Passbook" Modal

This modal provides a comprehensive, read-only view of the account's history and performance.

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ PPF Account: Test PPF Bank (123456789)                                             [X]│
│ Opened on: 01 Jan 2023                                                                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │ Total Contrib. │ Interest Earned│ Current Balance│ Annualized Ret.│ Current Rate │  │
│  │  ₹10,000.00    │  +₹1,455.00    │  ₹11,455.00    │    8.15%       │    7.10%     │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘  │
│                                                                                        │
│  Transaction History                                                                   │
│ ┌──────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ Date        | Description              | Amount          | Balance         | Actions │ │
│ ├─────────────┼──────────────────────────┼─────────────────┼─────────────────┼─────────┤ │
│ │ 31 Mar 2024 | Interest Credit FY 23-24 | + ₹710.00       | ₹10,710.00      | System  │ │
│ │ 20 May 2022 | Contribution             | + ₹10,000.00    | ₹10,000.00      | [⚙]     │ │
│ └──────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```
*Note: The `[⚙]` icon indicates that only user-created `Contribution` rows will have edit/delete actions.*

### 3.4. Detailed User Workflow

The UI flow will be simplified by leveraging the "one PPF account per user" rule.

1.  The user clicks the "Add Transaction" button.
2.  In the modal, they select "PPF Account" from the "Asset Type" dropdown.
3.  The UI then checks if a PPF account already exists for the user.
    *   **If NO PPF account exists:** The form shows fields to create the account (Institution, Account #, Opening Date) AND fields for the initial contribution (Amount, Date). The user fills everything and saves.
    *   **If a PPF account DOES exist:** The form displays the existing account details as read-only text and only shows the fields for a new contribution (Amount, Date).

### 3.5. User Workflow for Historical Data

To track an existing PPF account, the user follows this process:
1.  **Create the PPF Asset:** The user first creates the "PPF Account" asset with the correct opening date and their first historical contribution.
2.  **Log All Past Contributions:** The user then adds all other historical contributions as individual `CONTRIBUTION` transactions with their correct dates.
3.  **Automated Calculation:** The system automatically calculates the interest for each past financial year based on the logged contributions and the stored historical interest rates. It creates the necessary read-only `INTEREST_CREDIT` transactions.

**Note:** Users cannot manually add or edit the interest. The system's automated calculation, based on user-provided contributions, is the single source of truth for interest credits.
---

## 4. Backend Requirements

### 4.1. Database Schema Changes

*   **`Asset` Model (`models/asset.py`):**
    *   The `Asset` model will be updated with two new nullable columns: `account_number: Optional[str]` and `opening_date: Optional[date]`. This is the most pragmatic approach to store PPF-specific data without creating a new satellite table.
*   **`TransactionType` Enum (`schemas/transaction.py`):**
    *   A new value, `CONTRIBUTION`, will be added to the `TransactionType` enum.
*   **`AssetType` Enum (`schemas/asset.py`):**
    *   A new value, `PPF`, will be added to the `AssetType` enum.
*   **New Table: `historical_interest_rates`:**
    *   A new global table will be created to store historical interest rates for various government schemes.
    *   **Columns:** `id`, `scheme_name` (e.g., "PPF"), `start_date`, `end_date`, `rate`.
    *   **Data Source:** The historical data for PPF rates will be seeded from `backend/app/db/seed_data/ppf_interest_rates.py`.

### 4.2. API Endpoints

*   **Asset Creation:** The existing `POST /api/v1/assets/` endpoint will be used. The `AssetCreate` schema will be updated to accept the new optional `account_number` and `opening_date` fields.
*   **Contribution Creation:** The existing `POST /portfolios/{id}/transactions` endpoint will be used, with `transaction_type: 'CONTRIBUTION'`.
*   **Interest Rate Management (Admin):** A new set of admin-only endpoints will be created under `/api/v1/admin/interest-rates` for full CRUD operations on the `historical_interest_rates` table.

### 4.3. Valuation Logic (`crud_holding.py`)

A new function will be implemented to calculate the PPF balance dynamically. It will fetch all `CONTRIBUTION` transactions for the PPF asset and apply interest based on the stored official rates.

*   **Accurate Monthly Calculation:**
    *   The logic iterates month-by-month for each financial year.
    *   For each month, it determines the minimum balance between the 5th and the end of the month, including any contributions made on or before the 5th.
    *   It looks up the applicable annual interest rate for that specific month from the `historical_interest_rates` table and calculates the monthly interest on this minimum balance (`applicable_rate / 12`).
    *   The sum of all monthly interest amounts for a financial year is credited on March 31st.
*   **Interest as Transaction (On-Demand Calculation):** The system does not use a background job. The interest calculation is triggered dynamically whenever a user's holdings are calculated (e.g., when viewing the portfolio). The logic iterates through each financial year of the PPF's life.
    *   **For Completed Financial Years:** If an `INTEREST_CREDIT` transaction for a *completed* year is missing or outdated (because a contribution was added/edited), the system will calculate and create/update it on the spot.
    *   **For the Current Financial Year:** The interest is calculated on-the-fly to determine the holding's `current_value`, but the `INTEREST_CREDIT` transaction is **not** created in the database until the financial year has concluded. This ensures the `current_value` is always up-to-date, while the transaction history remains clean and accurate.

### 4.4. Recalculation & Correction Logic

*   **Trigger for Recalculation:** The recalculation process is triggered whenever a user creates, updates, or deletes a `CONTRIBUTION` transaction.
*   **Correction Process (Smart Recalculation):**
    1.  When a contribution is modified, the system identifies the financial year of the change.
    2.  It then deletes all system-generated `INTEREST_CREDIT` transactions for that PPF asset from that financial year *onwards*. This is because a change in one year affects the opening balance of all subsequent years.
    3.  The next time holdings are calculated, the system will see the missing interest transactions and will re-calculate and create them sequentially, starting only from the first year that was invalidated. This avoids redundant calculations for unchanged years.
*   **Admin Corrections:** If an administrator corrects a historical interest rate, a background job or manual trigger should be available to re-calculate interest for all affected users and financial years.
---

## 5. Testing Plan

*   **Backend Unit Tests:**
    *   Write extensive tests for the new PPF interest calculation logic (Phase 1) against a known-correct spreadsheet calculation.
    *   Test the automatic creation of the `INTEREST_CREDIT` transaction at the end of a simulated financial year.
    *   Add tests for the new admin-only endpoints for managing historical interest rates.
*   **E2E Tests:**
    1. Create a PPF account.
    2. Add several contribution transactions.
    3. Verify the calculated `Current Balance` in the "Government Schemes" section is correct.
    4. Open the drill-down view and verify that both the `CONTRIBUTION` and the auto-generated `INTEREST_CREDIT` transactions are listed correctly.
        |----------------------------------------------------------------|
        | PPF Account: State Bank of India (12345)                       |
        | Opened on: 2023-01-01                                          |
        |----------------------------------------------------------------|
        | Total Contributions | Interest Earned | Current Balance | Annualized Return | Current Rate |
        | ₹1,00,000.00        | ₹16,740.09      | ₹1,16,740.09    | 8.15%             | 7.10%        |
        |----------------------------------------------------------------|
        | Date        | Description              | Amount        | Balance      |
        |-------------|--------------------------|---------------|--------------|
        | 31 Mar 2025 | Interest Credit FY 24-25 | + ₹7,739.07   | ₹1,16,740.09 |
        | 31 Mar 2024 | Interest Credit FY 23-24 | + ₹7,226.02   | ₹1,09,001.02 |
        | 01 Jan 2023 | Contribution             | + ₹1,00,000.00| ₹1,00,000.00 |
        |----------------------------------------------------------------|
        ```
    *   **Interest Rate Management (Admin):** A new UI in the "Admin Settings" area will allow an administrator to view and manage the historical PPF interest rates used in calculations.

### 3.1. Detailed User Workflow

The UI flow will be simplified by leveraging the "one PPF account per user" rule.

1.  The user clicks the "Add New..." button.
2.  In the modal, they select "PPF Account" from the "Asset Type" dropdown.
3.  The UI then checks if a PPF account already exists for the user.
    *   **If NO PPF account exists:** The form shows fields to create the account (Institution, Account #, Opening Date) AND fields for the initial contribution (Amount, Date). The user fills everything and saves.
    *   **If a PPF account DOES exist:** The form displays the existing account details as read-only text and only shows the fields for a new contribution (Amount, Date).

### 3.1. User Workflow for Historical Data

To track an existing PPF account, the user follows this process:
1.  **Create the PPF Asset:** The user first creates the "PPF Account" asset with the correct opening date.
2.  **Log All Past Contributions:** The user then adds all historical contributions as individual `CONTRIBUTION` transactions with their correct dates.
3.  **Automated Calculation:** The system automatically calculates the interest for each past financial year based on the logged contributions and the stored historical interest rates. It creates the necessary read-only `INTEREST_CREDIT` transactions.

**Note:** Users cannot manually add or edit the interest. The system's automated calculation, based on user-provided contributions, is the single source of truth for interest credits.
---

## 4. Backend Requirements

### 4.1. Database Schema Changes

*   **`Asset` Model (`models/asset.py`):**
    *   The `Asset` model will be updated with two new nullable columns: `account_number: Optional[str]` and `opening_date: Optional[date]`. This is the most pragmatic approach to store PPF-specific data without creating a new satellite table.
*   **`TransactionType` Enum (`schemas/transaction.py`):**
    *   A new value, `CONTRIBUTION`, will be added to the `TransactionType` enum.
*   **`AssetType` Enum (`schemas/asset.py`):**
    *   A new value, `PPF`, will be added to the `AssetType` enum.
*   **New Table: `historical_interest_rates`:**
    *   A new global table will be created to store historical interest rates for various government schemes.
    *   **Columns:** `id`, `scheme_name` (e.g., "PPF"), `start_date`, `end_date`, `rate`.
    *   **Data Source:** The historical data for PPF rates will be seeded from `backend/app/db/seed_data/ppf_interest_rates.py`. This seeding is handled automatically on application startup by the `init-db` command, as configured in `entrypoint.sh`.

### 4.2. API Endpoints

*   **Asset Creation:** The existing `POST /api/v1/assets/` endpoint will be used. The `AssetCreate` schema will be updated to accept the new optional `account_number` and `opening_date` fields.
*   **Contribution Creation:** The existing `POST /portfolios/{id}/transactions` endpoint will be used, with `transaction_type: 'CONTRIBUTION'`.
*   **Interest Rate Management (Admin):** A new set of admin-only endpoints will be created under `/api/v1/admin/interest-rates` for full CRUD operations on the `historical_interest_rates` table.

### 4.3. Valuation Logic (`crud_holding.py`)

A new function will be implemented to calculate the PPF balance dynamically. It will fetch all `CONTRIBUTION` transactions for the PPF asset and apply interest based on the stored official rates.

*   **Phase 1 (Simplified Annual Calculation):**
    *   For each financial year (Apr 1 - Mar 31), the logic will calculate the opening balance.
    *   It will sum all contributions made during that year.
    *   Interest for the year will be calculated on the `(opening balance + total contributions)`. This is a simplified but effective initial approach.
    *   The final `current_balance` is the sum of all contributions plus all calculated annual interest amounts.
*   **Phase 2 (Accurate Monthly Calculation - Future Enhancement):**
    *   The logic will be enhanced to iterate month-by-month.
    *   For each month, it will determine the minimum balance between the 5th and the end of the month.
    *   It will look up the applicable annual interest rate for that specific month from the `historical_interest_rates` table and calculate the monthly interest on this minimum balance (`applicable_rate / 12`).
    *   The sum of all monthly interest amounts for a financial year will be credited on March 31st.
*   **Interest as Transaction (On-Demand Calculation):** The system does not use a background job. The interest calculation is triggered dynamically whenever a user's holdings are calculated (e.g., when viewing the portfolio). The logic iterates through each financial year of the PPF's life.
    *   **For Completed Financial Years:** If an `INTEREST_CREDIT` transaction for a *completed* year is missing or outdated (because a contribution was added/edited), the system will calculate and create/update it on the spot.
    *   **For the Current Financial Year:** The interest is calculated on-the-fly to determine the holding's `current_value`, but the `INTEREST_CREDIT` transaction is **not** created in the database until the financial year has concluded. This ensures the `current_value` is always up-to-date, while the transaction history remains clean and accurate.

### 4.4. Recalculation & Correction Logic

*   **Trigger for Recalculation:** The recalculation process is triggered whenever a user creates, updates, or deletes a `CONTRIBUTION` transaction.
*   **Correction Process (Smart Recalculation):**
    1.  When a contribution is modified, the system identifies the financial year of the change.
    2.  It then deletes all system-generated `INTEREST_CREDIT` transactions for that PPF asset from that financial year *onwards*. This is because a change in one year affects the opening balance of all subsequent years.
    3.  The next time holdings are calculated, the system will see the missing interest transactions and will re-calculate and create them sequentially, starting only from the first year that was invalidated. This avoids redundant calculations for unchanged years.
*   **Admin Corrections:** If an administrator corrects a historical interest rate, a background job or manual trigger should be available to re-calculate interest for all affected users and financial years.
---

## 5. Testing Plan

*   **Backend Unit Tests:**
    *   Write extensive tests for the new PPF interest calculation logic (Phase 1) against a known-correct spreadsheet calculation.
    *   Test the automatic creation of the `INTEREST_CREDIT` transaction at the end of a simulated financial year.
    *   Add tests for the new admin-only endpoints for managing historical interest rates.
*   **E2E Tests:**
    1. Create a PPF account.
    2. Add several contribution transactions.
    3. Verify the calculated `Current Balance` in the "Government Schemes" section is correct.
    4. Open the drill-down view and verify that both the `CONTRIBUTION` and the auto-generated `INTEREST_CREDIT` transactions are listed correctly.
