# Feature Plan (v2): Public Provident Fund (PPF) Tracking

**Status: 📝 Planned**
---
**Feature ID:** FR4.3.4
**Title:** Revamp Public Provident Fund (PPF) Tracking with Automated Calculations
**User Story:** As a user, I want to track my PPF account with automated interest calculations based on official rates, so I can see its true growth without manual updates and have confidence in the data.

---

## 1. Objective

The initial MVP for PPF tracking relied on a user-managed `current_balance`, which is inaccurate and cumbersome. This plan details a full revamp to implement proper contribution tracking and automated, rule-based interest calculations.

---

## 2. UI/UX Requirements

*   **Sectioned View:** PPF accounts will be displayed within the new "Government Schemes" collapsible section in the main holdings table.
*   **Dedicated Columns:** The "Government Schemes" section will have columns relevant to PPF:
    *   **Columns:** Asset (e.g., "PPF Account"), Institution, Opening/Start Date, Current Balance.
*   **User Interactions:**
    *   The "Add PPF" form will be simplified to only require institution and opening date.
    *   Users will log all deposits using a "Contribution" transaction type.
    *   A new UI in the "Settings" area will allow users to view and manage the historical PPF interest rates used in calculations.

---

## 3. Backend Requirements

### 3.1. Database Schema Changes (`models.PublicProvidentFund`)

*   The `current_balance` field will be removed from the main PPF model, as it will now be calculated.
*   A new related table, `ppf_interest_rates`, will be created to store historical interest rates by quarter/year.
    *   `ppf_id`: Foreign Key (or make it a global table)
    *   `start_date`: Date
    *   `end_date`: Date
    *   `rate`: Numeric

### 3.2. Valuation Logic (`crud_holding.py`)

*   A new function will be implemented to calculate the PPF balance dynamically.
*   It will fetch all "Contribution" transactions for the PPF asset.
*   It will apply interest based on the stored official rates and government rules.
*   **MVP Calculation:** The initial calculation can be based on annual compounding on the year-end balance. (A future iteration can implement the more complex monthly minimum balance calculation).
*   **Interest as Transaction:** At the end of each financial year, the system will automatically create a read-only "Interest Credited" transaction for the calculated amount. This provides a clear, auditable history.

---

## 4. Testing Plan

*   **Backend Unit Tests:** Write extensive tests for the new PPF interest calculation logic against a known correct value using sample contributions and rate changes.
*   **E2E Tests:**
    1. Create a PPF account.
    2. Add several contribution transactions.
    3. Verify the calculated `Current Balance` in the "Government Schemes" section is correct.
    4. Verify the "Interest Credited" transaction is created at the end of a simulated financial year.

