# Feature Plan: Recurring Deposit (RD) Tracking

**Status: ✅ Done**
---
**Feature ID:** FR4.3.3
**Title:** Implement Tracking for Recurring Deposits (RDs)
**User Story:** As a user who makes systematic investments, I want to track my Recurring Deposits (RDs) within the application, so that I can monitor my regular savings, see their projected growth, and understand their performance with detailed analytics.

---

## 1. Objective

To provide a robust and accurate way for users to track their Recurring Deposits. This plan aligns with the v2 redesign of the holdings view, ensuring RDs are displayed clearly and logically.

---

## 2. UI/UX Requirements

*   **Sectioned View:** RDs are displayed within the "Deposits" collapsible section in the main holdings table.
*   **Dedicated Columns:** The "Deposits" section has columns relevant to RDs:
    *   **Columns:** Asset, Type (RECURRING_DEPOSIT), Interest Rate, Maturity Date, Total Invested, Current Value.
*   **Add Asset Flow:** The "Add Transaction" modal has been updated with a new form for creating RDs, capturing: institution name, account number, monthly installment amount, interest rate, start date, and tenure (in months).
*   **Drill-Down View:** A new `RecurringDepositDetailModal` has been created to show detailed information about an RD, including its projected maturity value and XIRR analytics.

---

## 3. Backend Requirements

### 3.1. Database Schema Changes

*   A new `RecurringDeposit` model has been created with fields for `name`, `account_number`, `monthly_installment`, `interest_rate`, `start_date`, and `tenure_months`.
*   A new Alembic migration script (`2fc13ed78a51`) has been created to add the `recurring_deposits` table and the `account_number` column.

### 3.2. Valuation Logic (`crud_holding.py` & `crud_analytics.py`)

*   **Total Invested Amount:** Calculated as `monthly_installment * number_of_installments_paid`.
*   **Current Value:** The `_calculate_rd_value_at_date` function has been implemented. It calculates the future value of each individual installment up to the calculation date, with quarterly compounding.
*   **XIRR:** The main portfolio XIRR calculation in `crud_analytics.py` has been updated to correctly include cash flows from RDs (installments as outflows, current value as a final inflow).

---

## 4. Technical Implementation

*   **Backend:**
    *   **Model:** `backend/app/models/recurring_deposit.py`
    *   **Schema:** `backend/app/schemas/recurring_deposit.py`
    *   **CRUD:** `backend/app/crud/crud_recurring_deposit.py`
    *   **API:** `backend/app/api/v1/endpoints/recurring_deposits.py` (and integrated into `portfolios.py`)
    *   **Migration:** `backend/alembic/versions/2fc13ed78a51_add_account_number_to_recurring_deposit.py`
*   **Frontend:**
    *   **Types:** `frontend/src/types/recurring_deposit.ts`
    *   **API Service:** `frontend/src/services/portfolioApi.ts`
    *   **Hooks:** `frontend/src/hooks/useRecurringDeposits.ts`
    *   **UI Components:**
        *   `frontend/src/components/Portfolio/TransactionFormModal.tsx` (updated)
        *   `frontend/src/components/Portfolio/RecurringDepositDetailModal.tsx` (new)

---

## 5. Testing Plan

*   **Backend Unit Tests:** The `test_recurring_deposit_valuation` test has been added to `test_recurring_deposits.py` to verify the valuation logic.
*   **E2E Tests:** A new test file, `e2e/tests/recurring-deposits.spec.ts`, has been created to validate the end-to-end flow of creating, viewing, and deleting an RD. All tests are passing.
