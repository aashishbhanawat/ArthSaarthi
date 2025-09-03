# Feature Plan: Advanced Asset Support (FR9)

**Status: ✅ Implemented**
---
***Note: This document has been updated to reflect the "as-built" implementation of the feature.***

**Feature ID:** FR9
**Title:** Add Support for Fixed-Income and Other Asset Classes
**User Story:** As a user, I want to be able to track my Fixed Deposits (FDs), Public Provident Fund (PPF), and Bonds alongside my stocks and mutual funds, so that I have a complete, holistic view of my entire investment portfolio in one place.

---

## 1. Objective

The current application excels at tracking market-linked securities like stocks and mutual funds. This feature will expand the application's capabilities to include common fixed-income and long-term savings instruments prevalent in the Indian market. This is a critical step towards making ArthSaarthi a comprehensive portfolio management tool.

---

## 2. Requirement Analysis

*This section describes the final implemented logic.*

### 2.1. Fixed Deposits (FDs)

#### Data Fields
*   **`institution_name`**: String (e.g., "HDFC Bank", "State Bank of India")
*   **`account_number`**: String (Optional, for user reference)
*   **`principal_amount`**: Numeric (The initial investment amount)
*   **`interest_rate`**: Numeric (Annual interest rate, e.g., 7.5 for 7.5%)
*   **`start_date`**: Date (The date the FD was opened)
*   **`maturity_date`**: Date (The date the FD matures)
*   **`payout_type`**: Enum (`REINVESTMENT`, `PAYOUT`) - Determines if interest is compounded or paid out.
*   **`compounding_frequency`**: Enum (e.g., `MONTHLY`, `QUARTERLY`, `HALF_YEARLY`, `ANNUALLY`, `AT_MATURITY`)

#### Valuation Logic
The valuation depends on the `payout_type`.
*   **For `REINVESTMENT` (Cumulative FDs):** The current value is the principal plus accrued compound interest. The formula is: `Current Value = P * (1 + r/n)^(n*t)`
    *   `P` = `principal_amount`
    *   `r` = `interest_rate` / 100
    *   `n` = Compounding periods per year (1 for Annually, 2 for Half-yearly, 4 for Quarterly, 12 for Monthly)
    *   `t` = Time in years from `start_date` to today.
*   **For `PAYOUT` (Non-Cumulative FDs):** The current value is simply the **`principal_amount`**. The periodic interest payments will be tracked as income, which is part of a separate, future feature (FR4.5).

#### User Interactions
Adding an FD is a one-time setup. The user will select "Add New Asset" -> "Fixed Income" -> "Fixed Deposit" and fill out a dedicated form. No "transactions" are associated with it.

#### Display Requirements
In the main holdings table, FDs should display:
*   **Asset Name:** `institution_name` (e.g., "HDFC Bank FD")
*   **Key Metric 1:** Interest Rate (e.g., "7.50%")
*   **Key Metric 2:** Maturity Date
*   **Current Value:** The calculated current value.

---

## 3. Testing Plan

This feature requires a multi-layered testing approach to ensure data integrity, calculation accuracy, and a seamless user experience.

### 3.1. Backend Testing (Unit & Integration)

*   **Database Migrations:**
    *   Verify that a new Alembic migration script is created and correctly adds the new tables (`fixed_income_details`, etc.) and any modifications to the `assets` table.
    *   Test that the migration can be applied and reverted successfully.
*   **CRUD & Business Logic:**
    *   Create a dedicated test suite for the new `crud_fixed_income.py` module.
    *   **FD Valuation:** Write specific unit tests to verify the compound interest calculation logic for FDs with different compounding frequencies (`MONTHLY`, `QUARTERLY`, `ANNUALLY`).
    *   **PPF Contributions:** Test that creating a `CONTRIBUTION` transaction correctly updates the `current_balance` of the corresponding PPF asset.
    *   **Holdings Integration:** Update tests for `crud_holding.py` to ensure that FDs, PPFs, and Bonds are correctly included in the main holdings list and that their values contribute accurately to the portfolio summary.
*   **API Endpoints:**
    *   Create a new test suite for the new asset creation endpoints (e.g., `test_fixed_income_assets.py`).
    *   Test for successful creation of each new asset type (FD, PPF, Bond).
    *   Test for validation errors (e.g., submitting an FD with a maturity date before the start date).
    *   Test for correct ownership and authorization rules.

### 3.2. Frontend Testing (Unit & Component)

*   **New Forms:**
    *   Create unit tests for the new "Add Fixed Deposit" and "Add Bond" forms.
    *   Verify that form validation works correctly for all new fields (e.g., interest rate must be a positive number).
*   **Holdings Table (`HoldingsTable.tsx`):**
    *   Update the unit tests for the holdings table.
    *   Add test cases to verify that it correctly renders rows for the new asset types, displaying the relevant data (e.g., "Maturity Date") and showing "N/A" for inapplicable columns.

### 3.3. End-to-End Testing (Playwright)

A new E2E test file, `e2e/tests/advanced-assets.spec.ts`, will be created to validate the full user flows.

*   **Test Case 1: Fixed Deposit Flow:**
    1.  Log in and navigate to a portfolio.
    2.  Use the "Add New Asset" flow to create a new Fixed Deposit.
    3.  Verify that the FD appears correctly in the holdings table with the correct calculated current value.
*   **Test Case 2: Public Provident Fund (PPF) Flow:**
    1.  Log in and navigate to a portfolio.
    2.  Use the "Add New Asset" flow to create a new PPF account.
    3.  Verify that the PPF account appears correctly in the holdings table.

### 2.2. Public Provident Fund (PPF)

#### Implementation Model
To simplify tracking and avoid the complexities of official interest calculations and contribution tracking, the implemented version of PPF tracking treats a PPF account as a simple, non-transactional asset, similar to a Fixed Deposit.

#### Data Fields
*   **`institution`**: String (e.g., "Post Office", "ICICI Bank")
*   **`account_number`**: String (Optional, for user identification)
*   **`principal`**: Numeric (The total amount invested to date)
*   **`interest_rate`**: Numeric (The current applicable annual interest rate)
*   **`opening_date`**: Date

#### Valuation Logic
The valuation uses a simplified compound interest formula, analogous to a reinvestment FD. This provides an estimated current value.
*   **Current Value = `P * (1 + r/n)^(n*t)`**
    *   `P` = `principal`
    *   `r` = `interest_rate` / 100
    *   `n` = 1 (compounded annually)
    *   `t` = Time in years from `opening_date` to today.

This approach deviates from the original plan of tracking individual contributions in favor of providing a simpler, more manageable user experience for the MVP.

#### User Interactions
Adding a PPF account is a one-time setup.
1.  The user selects "Add New Asset" -> "PPF Account".
2.  They fill out a dedicated form with the fields listed above.
3.  No "contribution" transactions are created. The user is expected to update the `principal` amount manually if they make new contributions.

#### Display Requirements
In the main holdings table, PPF should display:
*   **Asset Name:** `institution` (e.g., "Post Office PPF")
*   **Key Metric 1:** Interest Rate
*   **Key Metric 2:** Maturity Date (15 years from `opening_date`)
*   **Current Value:** The calculated current value.

---

### 2.3. Bonds

#### Data Fields
*   **`bond_name`**: String (e.g., "NHAI 5.5% 2030")
*   **`isin`**: String (Optional, for identification)
*   **`face_value`**: Numeric (The value at maturity, e.g., 1000)
*   **`coupon_rate`**: Numeric (Annual interest rate, e.g., 8.0 for 8.0%)
*   **`purchase_price`**: Numeric (The price paid per bond)
*   **`purchase_date`**: Date
*   **`maturity_date`**: Date
*   **`interest_payout_frequency`**: Enum (`ANNUALLY`, `SEMI_ANNUALLY`)
*   **`quantity`**: Integer (Number of bonds purchased)

#### Valuation Logic
For non-traded bonds held to maturity, the MVP will use a simplified book value.
*   **Current Value = `purchase_price * quantity`**.
*   Future enhancements will add accrued interest calculations.

#### User Interactions
Similar to FDs, this is a one-time setup. Unlike stocks or mutual funds, there is no integrated data source to search for bonds. The user must manually enter all details for the specific bond they have purchased.

1.  User selects "Add New Asset" -> "Fixed Income" -> "Bond".
2.  A dedicated form appears, and the user manually fills in all the data fields.

#### Display Requirements
In the main holdings table, Bonds should display:
*   **Asset Name:** `bond_name`
*   **Key Metric 1:** Coupon Rate
*   **Key Metric 2:** Maturity Date
*   **Current Value:** The calculated current value.

---