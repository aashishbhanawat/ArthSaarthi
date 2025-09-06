# Feature Plan: Fixed Deposit Holding Drill-Down View

**Status: ✅ Done**
---
**Feature ID:** FR4.7.4
**Title:** Create Detailed Drill-Down View for Fixed Deposits
**User Story:** As a user, when I click on one of my Fixed Deposits in the holdings table, I want to see a detailed view with all its specific parameters, current valuation, and projected maturity value, so I can fully understand my investment.

---

## 1. Objective

To create a dedicated, asset-appropriate drill-down view for Fixed Deposits (FDs). This view replaces the generic transaction list with a detailed summary of the FD's properties and valuation, and defines how the system handles matured and renewed FDs.

---

## 2. UI/UX Requirements

When a user clicks on an FD row in the "Deposits" section, a modal (`FixedDepositDetailModal.tsx`) displays the following information, grouped logically.

### 2.1. Mockup UI

```
  Holding Detail: HDFC Bank FD

  +-----------------------------------------------------------------+
  | Details                                                         |
  |-----------------------------------------------------------------|
  | Institution:         HDFC Bank                                  |
  | Principal Amount:    ₹100,000.00                                |
  | Interest Rate:       7.50% p.a.                                 |
  | Start Date:          2025-03-12                                 |
  | Maturity Date:       2026-03-12                                 |
  | Compounding:         Quarterly                                  |
  | Payout Type:         Cumulative                                 |
  +-----------------------------------------------------------------+

  +-----------------------------------------------------------------+
  | Valuation                                                       |
  |-----------------------------------------------------------------|
  | Current Value:       ₹104,557.77                                |
  | Unrealized Gain:     +₹4,557.77                                 |
  | Maturity Value:      ₹107,762.86 (Projected)                    |
  +-----------------------------------------------------------------+

  +-----------------------------------------------------------------+
  | Analytics (XIRR)                                                |
  |-----------------------------------------------------------------|
  | Annualized Return (XIRR):     7.50%                             |
  +-----------------------------------------------------------------+

  +-----------------------------------------------------------------+
  | Actions                                                         |
  |-----------------------------------------------------------------|
  | [ Edit FD Details ]  [ Delete FD ]                              |
  +-----------------------------------------------------------------+
```

---

## 3. Analytics & Calculations

### 3.1. XIRR for Fixed Deposits

*   **Annualized Return (XIRR):** For an active FD, this shows the time-weighted return to date. For a matured FD, this shows the final realized XIRR.

### 3.2. Valuation
*   **Current Value:** Calculated using the compound interest formula for cumulative FDs, or equal to principal for payout FDs.
*   **Maturity Value:** A projection of the FD's total value on its maturity date.

---

## 4. Handling Matured & Renewed Fixed Deposits

This section defines the system logic for FDs that have reached or passed their maturity date.

### 4.1. Matured FDs

*   **System Logic:** Implemented in `crud_holding.py`. Matured FDs are excluded from active holdings, and their gains are moved to the portfolio's `total_realized_pnl`.

### 4.2. Renewed FDs

*   **Core Principle:** A renewal is a new investment cycle and is stored as a new `FixedDeposit` record.

---

## 5. Implementation Details

*   **Frontend:**
    *   A new component `frontend/src/components/Portfolio/FixedDepositDetailModal.tsx` was created to render the modal.
    *   The data layer was updated with new API service functions (`fetchFdDetails`, `fetchFdAnalytics`) and React Query hooks to fetch the required data.
*   **Backend:**
    *   New endpoints were added to `backend/app/api/v1/endpoints/fixed_deposits.py` to serve the details (`GET /{fd_id}`) and analytics (`GET /{fd_id}/analytics`) for a single FD.
    *   The business logic for the analytics calculation was implemented in `backend/app/crud/crud_analytics.py`.