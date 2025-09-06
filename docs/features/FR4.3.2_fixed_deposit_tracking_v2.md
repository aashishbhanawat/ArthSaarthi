# Feature Plan (v2): Fixed Deposit (FD) Tracking

**Status: ✅ Done**
---
**Feature ID:** FR4.3.2
**Title:** Implement Tracking for Fixed Deposits (FDs)
**User Story:** As a user with diverse investments, I want to track my Fixed Deposits (FDs) within the application, so that I can have a complete, holistic view of my entire investment portfolio in one place.

---

## 1. Objective

To provide a robust and accurate way for users to track their Fixed Deposits. This feature includes the ability to create, view, and delete FDs, as well as view detailed analytics like XIRR.

---

## 2. UI/UX Requirements

*   **Sectioned View:** FDs are displayed within the "Deposits" collapsible section in the main holdings table.
*   **Dedicated Columns:** The "Deposits" section has columns relevant to FDs:
    *   **Columns:** Asset, Type (FD), Interest Rate, Maturity Date, Invested Amount, Current Value.
*   **Add Asset Flow:** A new "Fixed Deposit" option is available in the "Add Transaction" modal, with a dedicated form for FD creation.
*   **Drill-Down View:** A detailed drill-down modal is available for each FD, showing details, valuation, and XIRR analytics.
*   **Edit/Delete:** Users can edit and delete their FDs from the drill-down view.

---

## 3. Backend Requirements

*   **Data Model:** A new `fixed_deposits` table has been added to the database to store FD details.
*   **Valuation Logic:** The valuation logic in `crud_holding.py` correctly calculates the current value for both cumulative and payout FDs.
*   **XIRR Analytics:** The backend calculates both unrealized and realized XIRR for FDs.
*   **Matured FDs:** Matured FDs are excluded from the active holdings list, and their gains are moved to realized PNL.
*   **API Integration:** New API endpoints have been added for creating, reading, updating, deleting, and getting analytics for FDs.

---

## 4. Testing Plan

*   **E2E Tests:** E2E tests have been added to verify the end-to-end flow of creating, viewing, and deleting FDs.
*   **Backend Unit Tests:** Unit tests have been added for the new FD endpoints and analytics calculations.
*   **Frontend Component Tests:** Component tests have been added for the new FD-related components.

