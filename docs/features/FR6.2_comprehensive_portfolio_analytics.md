# Feature Plan: Comprehensive Portfolio Analytics

**Status: ✅ Done**
**Feature ID:** FR6.2
**Title:** Implement Comprehensive & Accurate Portfolio Analytics
**User Story:** As an investor, I want all income events (dividends, coupons, interest) to be accurately reflected in my portfolio's key performance indicators (Realized P&L, Total Value, XIRR), so I can have a true and complete understanding of my investment performance.

---

## 1. Objective

This feature addresses a critical gap identified during manual testing. The objective is to correctly and robustly implement the business logic required to factor in all cash-generating events (dividends, coupons, interest) into the portfolio's main analytics. This will be a backend-focused task, with a heavy emphasis on creating a comprehensive test suite to validate the financial logic across all scenarios.

The previous implementation attempt was reverted due to instability. This plan outlines a more structured, test-driven approach to re-implementing the logic correctly.

---

## 2. High-Level Requirements

1.  **Realized P&L:** The portfolio's total realized P&L must include all cash income from dividends, bond coupons, and matured deposits.
2.  **Total Portfolio Value:** The portfolio's total value must reflect the sum of the current market value of all held assets PLUS any cash income received.
3.  **Asset-Level XIRR (Current Holding):** A metric to show the performance of the shares an investor *currently holds*, including prorated income.
4.  **Asset-Level Historical XIRR:** A metric to show the total lifetime performance of an investment in a specific asset, including both open and closed positions.
5.  **Portfolio-Level XIRR:** The main portfolio XIRR must correctly account for all cash inflows and outflows across all asset types.

---

## 3. Detailed Feature Breakdown

### 3.1. Realized P&L Calculation (`crud_holding.py`)

*   **Requirement:** The `total_realized_pnl` calculated in `get_portfolio_holdings_and_summary` must be updated.
*   **Logic:**
    *   The loop processing transactions should be updated. When a `DIVIDEND` or `COUPON` transaction is encountered, its value (`quantity` * `price_per_unit`) must be added to the `total_realized_pnl` accumulator.
    *   This is in addition to the existing logic that calculates realized P&L from `SELL` transactions.

### 3.2. Total Portfolio Value Calculation (`crud_holding.py`)

*   **Requirement:** The `summary_total_value` must be corrected.
*   **Logic:**
    *   The final `summary_total_value` should be the sum of the `current_value` of all individual holdings (stocks, deposits, etc.).
    *   Crucially, we must then **add** the cash income received from non-sale events. A simple way to do this is to add the value of all `DIVIDEND` and `COUPON` transactions to the final `summary_total_value`.
    *   **Important:** We must *not* add the entire `total_realized_pnl`, as this would double-count the proceeds from sales (which are already reflected by the asset no longer being in the holdings).

### 3.3. Asset-Level "Unrealized XIRR" Calculation (`crud_analytics.py`)

*   **Requirement:** The `unrealized_xirr` for a single asset must represent its **total return to date**, including income.
*   **Logic:**
    *   In `get_asset_analytics`, the cash flows for the `unrealized_xirr` calculation should be constructed as follows:
        1.  Start with the `unrealized_cash_flows` (which contains the cost basis of currently held shares).
        2.  Add all positive `realized_cash_flows` (which contains income from dividends and coupons, as well as proceeds from sales).
        3.  Add the final `current_value` of the holding as the terminal cash inflow.
    *   This provides a complete picture of the asset's performance, answering the question: "Based on what I paid, what I've received in cash, and what it's worth now, what is my annualized return?"

### 3.4. Portfolio-Level XIRR Calculation (`crud_analytics.py`)

*   **Requirement:** The main portfolio XIRR calculation in `get_portfolio_analytics` must be corrected.
*   **Logic:**
    *   The loop that aggregates cash flows needs to be fixed to handle the direction of flows correctly for all transaction types.
    *   **Outflows (Negative):**
        *   `BUY` (for Stocks, MFs, Bonds)
        *   `CONTRIBUTION` (for PPF)
        *   Principal investment for Fixed Deposits.
        *   Installments for Recurring Deposits.
    *   **Inflows (Positive):**
        *   `SELL` (for Stocks, MFs, Bonds)
        *   `DIVIDEND`
        *   `COUPON`
        *   `INTEREST_CREDIT`
        *   Maturity value for matured Fixed/Recurring Deposits.
    *   The final `total_value` of the portfolio is the terminal positive cash inflow.

---

## 4. Testing Plan

This feature must be test-driven. We will add new, failing tests first, then implement the logic to make them pass.

### 4.1. Backend Unit & Integration Tests

*   **`test_holdings.py`:**
    *   Create a new test, `test_summary_with_dividend`, that:
        1.  Creates a holding.
        2.  Adds a `DIVIDEND` transaction.
        3.  Calls the `/summary` endpoint.
        4.  Asserts that `total_realized_pnl` is equal to the dividend amount.
        5.  Asserts that `total_value` is equal to the holding's `current_value` plus the dividend amount.

*   **`test_analytics.py`:**
    *   Create a new test, `test_asset_xirr_with_dividend`, that:
        1.  Creates a holding with a `BUY` transaction.
        2.  Adds a `DIVIDEND` transaction.
        3.  Calls the `/assets/{id}/analytics` endpoint.
        4.  Asserts that the `xirr` and `historical_xirr` are specific, pre-calculated correct values that account for the dividend and proration logic.

*   **`test_bond_crud.py`:**
    *   The existing `test_bond_xirr_with_coupon_payment` already covers the asset-level XIRR for bonds. We will ensure it is passing after the refactor.

*   **`test_dashboard.py` / `test_analytics.py`:**
    *   Create a new test, `test_portfolio_xirr_with_dividend`, that:
        1.  Creates a portfolio with a stock holding and a dividend.
        2.  Calls the main portfolio analytics endpoint.
        3.  Asserts that the returned `xirr` is a specific, pre-calculated correct value.

### 4.2. Manual E2E Testing

*   After all automated tests are passing, a full manual E2E test will be performed, specifically focusing on:
    1.  Adding a dividend to a stock and verifying the main dashboard summary updates correctly.
    2.  Verifying the "Realized P&L" and "Total Value" on the portfolio detail page are correct.
    3.  Verifying the "XIRR (Current)" and "Historical XIRR" in the holding drill-down modal are correct.
    4.  Verifying the main portfolio "XIRR" on the portfolio detail page's analytics card is correct.

---

## 5. Implementation Plan (Revised for Incremental Development)

To avoid the instability of the previous attempt, we will follow a strict, incremental, test-driven approach. We will tackle one piece of the calculation at a time, ensuring the entire test suite passes after every single change.

1.  **Establish Baseline:** Run the full existing test suite (`backend`, `frontend`, `e2e`) to confirm a 100% "green" state before making any changes.

2.  **Stage 1: `total_realized_pnl` Correction.**
    *   **Task:** Add a single failing test (`test_summary_with_dividend`) that only checks if `total_realized_pnl` correctly includes dividend income.
    *   **Implement:** Make the minimal change in `crud_holding.py` to make this test pass.
    *   **Verify:** Run the full test suite to ensure no regressions.

3.  **Stage 2: `total_value` Correction.**
    *   **Task:** Update the same test (`test_summary_with_dividend`) to also assert the correct `total_value` (current market value + cash from dividends). This test will now fail again.
    *   **Implement:** Make the minimal change in `crud_holding.py` to correct the `total_value` calculation.
    *   **Verify:** Run the full test suite.

4.  **Stage 3: Portfolio-level XIRR Correction.**
    *   **Task:** Add a new failing test (`test_portfolio_xirr_with_dividend`) to `test_dashboard.py` that verifies the main portfolio XIRR calculation includes dividend cash flows.
    *   **Implement:** Fix the cash flow aggregation logic in `crud_analytics.py`.
    *   **Verify:** Run the full test suite.

5.  **Stage 4: Asset-level XIRR Correction.**
    *   **Task:** Add the final failing test (`test_asset_xirr_with_dividend`) to `test_analytics.py`.
    *   **Implement:** Fix the asset-level XIRR logic in `crud_analytics.py`.
    *   **Verify:** Run the full test suite.

6.  **Stage 5: Cleanup & Finalization.**
    *   **Task:** Remove any temporary debug logs and update all project documentation.
    *   **Verify:** Final manual E2E test.