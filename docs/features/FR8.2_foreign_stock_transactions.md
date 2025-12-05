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

*   **File to Modify:** `frontend/src/components/Portfolio/TransactionFormModal.tsx`.
*   **Conditional UI:** The modal will be enhanced to check the `currency` attribute of the selected asset.
    *   If `asset.currency` is not 'INR', the "INR Conversion" section will be rendered.
    *   If `asset.currency` is 'INR', the section will remain hidden, providing a clean UI for domestic stock transactions.
*   **API Call:** When the transaction date is selected for a foreign asset, the frontend will automatically call the `GET /api/v1/fx-rate` endpoint to fetch the historical exchange rate.

### 3.4. Backend Analytics (`crud_holding.py`)

The holdings calculation logic must be updated to correctly use the stored exchange rate.

*   **File to Modify:** `backend/app/crud/crud_holding.py`.
*   **Logic Update:** In the `_process_market_traded_assets` function, when processing `BUY` and `SELL` transactions:
    *   The code must check if `transaction.metadata` contains an `exchange_rate_to_inr` key.
    *   If it does, the `total_invested` amount (for `BUY`) and the `realized_pnl_for_sale` (for `SELL`) must be calculated using the price multiplied by this exchange rate.
    *   If it does not, the logic proceeds as normal, assuming the transaction was in INR.

## 4. Testing Plan

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