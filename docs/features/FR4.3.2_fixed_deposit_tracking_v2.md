# Feature Plan (v2): Fixed Deposit (FD) Tracking

**Status: 📝 Planned**
---
**Feature ID:** FR4.3.2
**Title:** Implement Tracking for Fixed Deposits (FDs)
**User Story:** As a user with diverse investments, I want to track my Fixed Deposits (FDs) within the application, so that I can have a complete, holistic view of my entire investment portfolio in one place.

---

## 1. Objective

To provide a robust and accurate way for users to track their Fixed Deposits. This plan aligns with the v2 redesign of the holdings view, ensuring FDs are displayed clearly and logically.

---

## 2. UI/UX Requirements

*   **Sectioned View:** FDs will be displayed within the new "Fixed Income" collapsible section in the main holdings table, as defined in the `Holdings Table Redesign` feature plan.
*   **Dedicated Columns:** The "Fixed Income" section will have columns relevant to FDs:
    *   **Columns:** Asset, Type (FD), Interest Rate, Maturity Date, Invested Amount, Current Value.
*   **Add Asset Flow:** The existing "Add Fixed Deposit" form will be used.

---

## 3. Backend Requirements

*   **Data Model:** The existing `FixedDeposit` model is sufficient and captures all necessary details.
*   **Valuation Logic:** The existing valuation logic in `crud_holding.py` is correct (assuming the `AT_MATURITY` bug is fixed).
    *   **Cumulative FDs:** `Current Value = P * (1 + r/n)^(n*t)`
    *   **Payout FDs:** `Current Value = Principal Amount`
*   **API Integration:** The holdings calculation logic must correctly categorize FDs to be grouped under the "Fixed Income" section in the API response.

---

## 4. Testing Plan

*   **E2E Tests:** Verify that a newly created FD appears in the "Fixed Income" section of the holdings table.
*   **Backend Unit Tests:** Ensure the valuation logic for both cumulative and payout FDs is correct.
*   **Frontend Component Tests:** Test the new `FixedIncomeRow` component to ensure it displays all data correctly.

