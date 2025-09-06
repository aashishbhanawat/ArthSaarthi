# Feature Plan (v2): Fixed Deposit (FD) Tracking

**Status: ✅ Done**
**Related Plans:** [FR4.7.4 (FD Drill-Down View)](./FR4.7.4_fd_holding_drilldown_view.md)
---
**Feature ID:** FR4.3.2
**Title:** Implement Tracking for Fixed Deposits (FDs)
**User Story:** As a user with diverse investments, I want to track my Fixed Deposits (FDs) within the application, so that I can have a complete, holistic view of my entire investment portfolio, including detailed analytics.

---

## 1. Objective

To provide a robust and accurate way for users to track their Fixed Deposits. This feature includes the ability to create, view, and delete FDs, as well as view detailed analytics like XIRR.

---

## 2. UI/UX Requirements

*   **Sectioned View:** FDs are displayed within the "Deposits" collapsible section in the main holdings table.
*   **Holdings Table Columns:** The "Deposits" section has columns relevant to FDs: Asset, Type (FD), Interest Rate, Maturity Date, Invested Amount, Current Value.
*   **Add Asset Flow:** A new "Fixed Deposit" option is available in the "Add Transaction" modal (`TransactionFormModal.tsx`), with a dedicated form for capturing FD details.
*   **Drill-Down View (`FixedDepositDetailModal.tsx`):** A detailed drill-down modal is available for each FD, showing:
    *   **Details Section:** Institution, Principal Amount, Interest Rate, Start/Maturity Dates, Compounding, and Payout Type.
    *   **Valuation Section:** Current Value, Unrealized/Realized Gain, and a projected Maturity Value.
    *   **Analytics Section:** A clear, intuitive display of the investment's annualized return (XIRR).
    *   **Actions:** Buttons to edit or delete the FD.

---

## 3. Backend Requirements

*   **Data Model (`models/fixed_deposit.py`):** A new `fixed_deposits` table was added to the database with columns for `principal_amount`, `interest_rate`, `start_date`, `maturity_date`, `compounding_frequency`, and `payout_type`.
*   **Valuation Logic (`crud/crud_holding.py`):**
    *   The `get_portfolio_holdings_and_summary` function was updated to calculate the current value for both cumulative (compound interest) and payout (principal value) FDs.
    *   It correctly identifies matured FDs, excludes them from active holdings, and adds their total interest to the portfolio's `total_realized_pnl`.
*   **Analytics Logic (`crud/crud_analytics.py`):**
    *   The `get_fixed_deposit_analytics` function calculates the XIRR for a single FD.
    *   The main portfolio XIRR calculation (`_calculate_xirr`) was refactored to correctly include cash flows from all FDs (principal investment, periodic payouts, and final maturity/current value).
*   **API Integration (`api/v1/endpoints/fixed_deposits.py`):**
    *   New endpoints were added for full CRUD operations on FDs.
    *   A dedicated `/analytics` endpoint was added to provide XIRR calculations for the drill-down view.

---

## 4. Testing Plan

*   **E2E Tests:** New tests were added to `e2e/tests/portfolio-and-dashboard.spec.ts` to verify the end-to-end flow of creating an FD and seeing it appear correctly in the holdings table.
*   **Backend Unit Tests (`tests/api/v1/test_fixed_deposits.py`):** A new test suite was added to verify the creation, reading, and analytics endpoints for FDs.
*   **Frontend Component Tests:** New tests were added for `FixedDepositDetailModal.tsx` and the FD-specific parts of `TransactionFormModal.tsx`.
