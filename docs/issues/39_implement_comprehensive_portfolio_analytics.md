---
name: '🚀 Feature Request'
about: 'Implement comprehensive and accurate portfolio analytics'
title: 'feat: Implement Comprehensive Portfolio Analytics (FR6.2)'
labels: 'enhancement, feature, backend, epic:analytics'
assignees: ''
---

### 1. User Story

**As an** investor,
**I want** all income events (dividends, coupons, interest) to be accurately reflected in my portfolio's key performance indicators (Realized P&L, Total Value, XIRR),
**so that** I can have a true and complete understanding of my investment performance.

---

### 2. Functional Requirements

*   [ ] **Realized P&L:** The portfolio's total realized P&L must include all cash income from dividends, bond coupons, and matured deposits.
*   [ ] **Total Portfolio Value:** The portfolio's total value must reflect the sum of the current market value of all held assets PLUS any cash income received.
*   [ ] **Asset-Level Unrealized XIRR:** The "Unrealized XIRR" for a single asset must be a "Total Return" calculation, including intermediate cash flows like dividends and coupons.
*   [ ] **Portfolio-Level XIRR:** The main portfolio XIRR must correctly account for all cash inflows (sales, dividends, coupons, interest) and outflows (buys, contributions) across all asset types.

---

### 3. Acceptance Criteria

*   [ ] **Realized P&L:** After adding a dividend, the portfolio summary's `total_realized_pnl` is correctly increased by the dividend amount.
*   [ ] **Total Value:** After adding a dividend, the portfolio summary's `total_value` is correctly increased by the dividend amount.
*   [ ] **Asset XIRR:** After adding a dividend or coupon to an asset, the asset's `unrealized_xirr` is correctly recalculated to reflect this income.
*   [ ] **Portfolio XIRR:** After adding a dividend, the main portfolio's `xirr` is correctly recalculated.
*   [ ] All new and existing backend tests must pass.
*   [ ] Manual E2E testing confirms the metrics are correct in the UI.

---

### 4. Implementation Plan

1.  **Write Tests First:** Implement all the new failing tests described in the feature plan.
2.  **Refactor `crud_holding.py`:** Refactor the `get_portfolio_holdings_and_summary` function into smaller, modular helper functions.
3.  **Fix `crud_holding.py`:** Implement the logic changes for `total_realized_pnl` and `total_value`.
4.  **Fix `crud_analytics.py` (Asset-Level):** Implement the logic changes for the asset-level `unrealized_xirr`.
5.  **Fix `crud_analytics.py` (Portfolio-Level):** Implement the logic changes for the main portfolio XIRR.
6.  **Manual Verification:** Perform a full manual E2E test.

---

### 5. Additional Context

*   **Requirement ID:** `FR6.2`
*   This feature addresses a critical gap identified during manual testing. The previous implementation attempt was reverted due to instability. This plan outlines a more structured, test-driven approach to re-implementing the logic correctly.
