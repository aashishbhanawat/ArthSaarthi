# FR4.4.3: Specific Lot Identification for Sales (Tax Lot Accounting)

**Status: ✅ Implemented**

## 1. Introduction

This document outlines the plan to implement "Specific Lot Identification" (also known as Tax Lot Accounting). This feature allows users to select the exact lots of shares they are selling, rather than having the system assume a default accounting method like FIFO (First-In, First-Out).

**User Story:** "As an investor who uses specific identification to manage my capital gains, I want to select the exact lots of shares I am selling, so that the application's realized P&L calculation matches my brokerage records and tax reporting."

## 2. Problem Description

The current system calculates realized profit and loss by assuming a default accounting method (e.g., FIFO). This is inaccurate for users who intentionally sell specific lots of shares (e.g., those with the highest cost basis) to minimize their tax liability. This is a very common and critical practice for investors with shares acquired at different prices and dates, especially through ESPP and RSU plans.

## 3. Proposed Solution

We will enhance the `SELL` transaction flow to allow users to specify the source lots for the shares being sold. This involves changes to the backend data model, the backend analytics logic, and the frontend UI.

### 3.1. Database Schema Changes

A new linking table, `transaction_links`, will be created to establish a many-to-many relationship between `SELL` transactions and their source acquisition transactions.

**`transaction_links` Table:**
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY` | Unique identifier for the link. |
| `sell_transaction_id` | `UUID` | `FOREIGN KEY (transactions.id)` | The `SELL` transaction. |
| `buy_transaction_id` | `UUID` | `FOREIGN KEY (transactions.id)` | The source `BUY`/`RSU_VEST`/`ESPP_PURCHASE` transaction. |
| `quantity` | `Numeric` | `NOT NULL` | The number of shares from this specific `buy_transaction_id` that are part of the sale. |

### 3.2. Backend Logic Changes

*   **Realized P&L Calculation:** The `crud_holding` and `crud_analytics` modules must be refactored. When calculating the cost basis for a `SELL` transaction, the logic must now query the `transaction_links` table to find the exact source `BUY` transactions and their corresponding quantities and prices. The FIFO assumption will be removed entirely in favor of this explicit link.
*   **API Endpoint:** The `POST /transactions` endpoint will be updated. When creating a `SELL` transaction, it will also accept a list of `links` to be created in the `transaction_links` table.

### 3.3. Frontend UI/UX Flow

The "Add Transaction" modal for a `SELL` operation will be significantly enhanced.

1.  User selects the asset and `Transaction Type: SELL`.
2.  User enters the `Sale Date`, `Total Quantity` to sell, and `Sale Price`.
3.  A new section, "Specify Lots to Sell", appears. This section lists all available acquisition lots for that asset (from `BUY`, `RSU_VEST`, `ESPP_PURCHASE` transactions) that have a remaining quantity.
4.  The user can manually enter the quantity to sell from each lot. The UI will validate that the sum of specified lots equals the total sale quantity.
5.  To improve user experience, helper buttons like "Apply FIFO", "Apply LIFO", and "Apply Highest Cost" will be provided to auto-fill the lot selections.

#### Mockup: `SELL` Transaction with Lot Selection

```
+------------------------------------------------------+
| Add Transaction                                [ X ] |
+------------------------------------------------------+
|                                                      |
|  Asset:          [ Google (GOOGL)           | v ]   |
|  Transaction Type:[ SELL                     | v ]   |
|                                                      |
|  Sale Date:      [ 2026-02-15               | 📅 ]   |
|  Total Quantity: [ 8.00000000                     ]   |
|  Sale Price:     [ 190.00                       ] USD |
|                                                      |
|  ---------- Specify Lots to Sell (8 / 8 filled) ---------   |
|  [Apply FIFO] [Apply LIFO] [Apply Highest Cost]      |
|                                                      |
|  Lot 1 (RSU Vest on 2025-11-15)                      |
|  Available: 6.00  |  Cost Basis: $150.25 (FMV)       |
|  Sell from this lot: [ 6.00000000 ]                   |
|                                                      |
|  Lot 2 (ESPP Purchase on 2025-12-01)                 |
|  Available: 25.00 |  Cost Basis: $170.00             |
|  Sell from this lot: [ 2.00000000 ]                   |
|                                                      |
|                           +--------------------+     |
|                           |   Record Sale      |     |
|                           +--------------------+     |
+------------------------------------------------------+
```

## 4. Testing Plan

### 4.1. Backend Unit & Integration Tests

*   **Test `transaction_links` Creation:**
    *   When creating a `SELL` transaction with lot information, verify that records are created in the new `transaction_links` table.
    *   Assert that the sum of quantities in the linked records equals the total sale quantity.
*   **Test Realized P&L Calculation:**
    *   Create a holding with multiple `BUY` lots at different prices.
    *   Create a `SELL` transaction that specifies selling the highest-cost lot.
    *   Call the holdings/analytics endpoint and assert that the `realized_pnl` is calculated based on the specified lot's cost basis, not FIFO.
*   **Test Validation:**
    *   Attempt to create a `SELL` transaction where the sum of specified lot quantities does not match the total sale quantity. Assert that the API returns a validation error.
    *   Attempt to sell more shares from a lot than are available. Assert that the API returns a validation error.

### 4.2. Frontend Component Tests (`TransactionFormModal.tsx`)

*   **Test UI Visibility:**
    *   Assert that the "Specify Lots to Sell" section appears only for `SELL` transactions and is hidden for `BUY`.
*   **Test Lot Data Display:**
    *   Mock the API that fetches available lots for an asset.
    *   Assert that the lots are displayed correctly with their remaining quantities and cost basis.
*   **Test Helper Buttons:**
    *   Simulate a click on the "Apply FIFO" and "Apply Highest Cost" helper buttons.
    *   Assert that the quantities in the lot input fields are auto-filled correctly based on the chosen strategy.
*   **Test Form Validation:**
    *   Assert that the "Record Sale" button is disabled if the specified lot quantities do not sum up to the total sale quantity.

### 4.3. End-to-End (E2E) Tests

*   **Full Lot Selection Flow:**
    1.  Create a holding with at least two `BUY` lots at different prices.
    2.  Open the "Add Transaction" modal and select `SELL`.
    3.  Verify the lot selection UI appears and displays the correct lots.
    4.  Manually specify quantities to sell from each lot (e.g., in LIFO order).
    5.  Commit the sale.
    6.  Navigate to the portfolio analytics and verify the `realized_pnl` reflects the specific lots sold, not the FIFO default.