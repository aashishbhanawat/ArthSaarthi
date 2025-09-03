# Feature Plan (v2): Recurring Deposit (RD) Tracking

**Status: 📝 Planned**
---
**Feature ID:** FR4.3.2
**Title:** Implement Tracking for Recurring Deposits (RDs)
**User Story:** As a user who makes systematic investments, I want to track my Recurring Deposits (RDs) within the application, so that I can monitor my regular savings and see their projected growth.

---

## 1. Objective

To provide a robust and accurate way for users to track their Recurring Deposits. This plan aligns with the v2 redesign of the holdings view, ensuring RDs are displayed clearly and logically.

---

## 2. UI/UX Requirements

*   **Sectioned View:** RDs will be displayed within the "Fixed Income" collapsible section in the main holdings table.
*   **Dedicated Columns:** The "Fixed Income" section will have columns relevant to RDs:
    *   **Columns:** Asset, Type (RD), Interest Rate, Maturity Date, Total Invested, Current Value.
*   **Add Asset Flow:** A new "Add Recurring Deposit" form will be created, capturing: institution name, monthly installment amount, interest rate, start date, and tenure (in months).

---

## 3. Backend Requirements

### 3.1. Database Schema Changes

*   A new `RecurringDeposit` model will be created with fields for `monthly_installment`, `interest_rate`, `start_date`, and `tenure_months`.

### 3.2. Valuation Logic (`crud_holding.py`)

*   **Total Invested Amount:** This will be calculated as `monthly_installment * number_of_months_passed`.
*   **Current Value:** This is the most complex calculation. It requires a function that calculates the future value of each installment paid to date, compounded quarterly (as is standard for most Indian RDs). The sum of these future values will be the `current_value`.
*   **Maturity Value (for display in detail view):** The system will also need a function to calculate the total projected value at the end of the full tenure.

---

## 4. Testing Plan

*   **Backend Unit Tests:** Write extensive tests for the RD valuation logic against a known correct value using a sample RD.
*   **E2E Tests:** Create a new RD and verify that it appears correctly in the "Fixed Income" section with the correct `Total Invested` and `Current Value`.

