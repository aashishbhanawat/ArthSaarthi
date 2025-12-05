# FR8.2: Foreign Stock Transaction Enhancements

**Status: 📝 Proposed**

## 1. Introduction

This document outlines the plan to enhance the standard "Add Transaction" modal to support `BUY` and `SELL` transactions for stocks denominated in foreign currencies (e.g., USD).

**User Story:** "As a user who invests in US-listed stocks, I want to record my buy and sell transactions in their original currency (USD) and have the system automatically handle the conversion to my portfolio's base currency (INR), so my cost basis and profit/loss are calculated accurately."

## 2. Problem Description

The current "Add Transaction" form for stocks implicitly assumes all transactions are in INR. It lacks fields to input a price in a foreign currency (like USD) and the corresponding exchange rate on the transaction date. This makes it impossible to accurately track the cost basis and performance of foreign investments.

## 3. Proposed Solution

We will enhance the standard `BUY`/`SELL` transaction modal to conditionally display a currency conversion section when the selected asset is denominated in a currency other than INR.

### 3.1. UI/UX Mock-up

When a user selects a foreign asset (e.g., Google, which is in USD), the form will dynamically include an "INR Conversion" section.

**Mockup: Selling a Foreign Stock**
```
+------------------------------------------------------+
| Add Transaction                                [ X ] |
+------------------------------------------------------+
|                                                      |
|  Asset:          [ Google (GOOGL)           | v ]   |
|  Transaction Type:[ SELL                     | v ]   |
|                                                      |
|  Sale Date:      [ 2026-01-20               | 📅 ]   |
|  Quantity:       [ 6.00000000                     ]   |
|  Sale Price:     [ 180.00                       ] USD |
|                                                      |
|  ----------------- INR Conversion -----------------   |
|  FX Rate (USD-INR): [ 84.10 (auto-fetched)         ]   |
|  Total Proceeds (INR):[ ₹90,828.00 (read-only)      ]   |
|                                                      |
|                           +--------------------+     |
|                           |   Record Sale      |     |
|                           +--------------------+     |
+------------------------------------------------------+
```
*This same logic will apply to `BUY` transactions.*

### 3.2. Backend Logic

*   This feature will leverage the `metadata` JSON column on the `transactions` table, which was introduced in `FR8.1.1`.
*   For any `BUY` or `SELL` transaction involving a foreign currency, the `exchange_rate_to_inr` will be stored in the `metadata` field.
*   This ensures that all P&L and cost basis calculations can be performed accurately in the portfolio's base currency (INR).

### 3.3. Frontend Logic

*   **Files to Modify:** `frontend/src/components/Portfolio/TransactionFormModal.tsx` and any component displaying currency.
*   **Conditional UI:** The modal will be enhanced to check the `currency` attribute of the selected asset.
    *   If `asset.currency` is not 'INR', the "INR Conversion" section will be rendered.
    *   If `asset.currency` is 'INR', the section will remain hidden, providing a clean UI for domestic stock transactions.
*   **API Call:** When the transaction date is selected for a foreign asset, the frontend will automatically call the `GET /api/v1/fx-rate` endpoint to fetch the historical exchange rate.
*   **Currency Display Standard:** All monetary values for foreign assets must be displayed using the `usePrivacySensitiveCurrency` hook, passing both the value and the asset's native currency (e.g., `formatCurrency(180.00, 'USD')`). This ensures consistent and accurate currency symbol rendering throughout the application.

### 3.4. Backend Analytics (`crud_holding.py`)

The holdings calculation logic must be updated to correctly use the stored exchange rate.
**Status: ✅ Done**

*   **File to Modify:** `backend/app/crud/crud_holding.py`.
*   **Logic Update:** In the `_process_market_traded_assets` function, when processing `BUY` and `SELL` transactions:
    *   The code must check if `transaction.details` contains an `fx_rate` key.
    *   If it does, the `total_invested` amount (for `BUY`) and the `realized_pnl_for_sale` (for `SELL`) must be calculated using the price multiplied by this exchange rate.
    *   If it does not, the logic proceeds as normal, assuming the transaction was in INR.
 
## 5. ESPP/RSU Analytics and UI Enhancements
 
This section details the necessary fixes and improvements to fully integrate ESPP/RSU transactions into the application's analytics and UI.
 
### 5.1. Portfolio History Chart Integration
 
*   **Problem:** The "Portfolio History" chart on the dashboard does not correctly factor in the value of assets acquired in a foreign currency (e.g., via `RSU_VEST`, `ESPP_PURCHASE`, or a standard `BUY`), leading to an inaccurate historical graph.
*   **Solution (Backend):** The logic for generating portfolio history (`crud_dashboard._get_portfolio_history`) must be updated. When calculating the portfolio value on a given day, it must correctly account for the value of all assets acquired on or before that day, applying the correct FX rate.
    *   For `RSU_VEST`, the value added to the portfolio is `quantity * fmv * fx_rate`.
    *   For `ESPP_PURCHASE` and standard `BUY` transactions, the value added is `quantity * price_per_unit * fx_rate`.
 
### 5.2. User-Friendly Transaction Details Modal
 
*   **Problem:** In the transaction history, hovering over the info icon for any transaction with extra details (like ESPP/RSU awards or any foreign currency transaction) shows raw, unformatted JSON, which is not user-friendly.
*   **Solution (Frontend):**
    *   Create a new reusable modal component, `TransactionDetailsModal.tsx`. This modal will receive a transaction object and display its `details` in a clean, readable format (e.g., "Fair Market Value: $150.25", "FX Rate: 83.50").
    *   In `TransactionHistoryTable.tsx`, the info icon for **any** transaction with a `details` field will now trigger this new modal instead of relying on a simple title attribute.
 
### 5.3. Holding Drill-Down Modal Enhancements
 
*   **Problem:** The holding drill-down modal has two issues for assets acquired via ESPP/RSU: it does not show these transaction types in its history, and the XIRR calculation is incorrect.
*   **Solution (Backend):**
    *   **Transaction Visibility:** The query that fetches transactions for the drill-down modal must be updated to include `RSU_VEST` and `ESPP_PURCHASE` types.
    *   **XIRR Calculation:** The XIRR logic in `crud_analytics.py` must be corrected.
        *   For `RSU_VEST` transactions, it must treat them as a cash outflow equal to `(FMV * Quantity * FX Rate)` on the vest date, as specified in `FR8.4`.
        *   For all other transaction types (`BUY`, `SELL`, `ESPP_PURCHASE`), the cash flow calculation must correctly use the `fx_rate` from the transaction's `details` when converting the value to INR.
 
## 6. Testing Plan

### 4.1. Backend Unit & Integration Tests

*   **Test Foreign `BUY`:**
    *   In `test_transactions.py`, create a test that adds a `BUY` transaction for a USD asset with an `exchange_rate_to_inr` in its metadata.
    *   Call the holdings endpoint and assert that the `total_invested_amount` for the holding is correctly calculated in INR (`quantity * price_usd * fx_rate`).
*   **Test Foreign `SELL`:**
    *   In `test_holdings.py`, create a test that adds a `BUY` (in USD) and then a `SELL` (in USD) for the same asset, each with an exchange rate in metadata.
    *   Call the portfolio summary endpoint and assert that the `total_realized_pnl` is calculated correctly in INR.

### 4.2. Frontend Component Tests (`TransactionFormModal.tsx`)

*   **Test Visibility (Domestic):**
    *   Render the modal and select an INR-based asset.
    *   Assert that the "INR Conversion" section is **not** in the document.
*   **Test Visibility (Foreign):**
    *   Render the modal and select a USD-based asset.
    *   Assert that the "INR Conversion" section **is** visible.
*   **Test FX Rate Fetch:**
    *   Mock the `fx-rate` API endpoint.
    *   Select a foreign asset and a date.
    *   Assert that the API was called and that the "FX Rate" and "Total (INR)" fields are populated correctly.

### 4.3. End-to-End (E2E) Tests

*   **Full Foreign Stock Lifecycle:**
    1.  Create a new portfolio.
    2.  Use the "Add ESPP/RSU Award" modal to add a foreign stock (e.g., Google) via an RSU vest.
    3.  Use the standard "Add Transaction" modal to `SELL` a portion of the acquired Google stock.
    4.  Verify the "INR Conversion" section appears and works correctly during the sale.
    5.  Submit the sale and verify that the portfolio summary (Realized P&L) and holdings (Quantity, Invested Amount) are updated correctly.

### 4.4. E2E Tests for ESPP/RSU Enhancements

*   **Test Portfolio History Chart:**
    1.  Add an RSU Vest transaction.
    2.  Verify that the "Portfolio History" chart on the dashboard shows an immediate increase in value corresponding to the FMV of the vested shares.
*   **Test Transaction Details Modal:**
    1.  Go to the Transaction History page.
    2.  Click the info icon on an RSU transaction.
    3.  Assert that a modal appears and displays the FMV and FX Rate in a user-friendly format.
*   **Test Holding Drill-Down:**
    1.  Click on a holding acquired via RSU.
    2.  Assert that the `RSU_VEST` transaction appears in the modal's transaction list.
    3.  Assert that the calculated XIRR is a non-zero, meaningful value.