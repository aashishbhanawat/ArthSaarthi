# FR8.1.1: Employee Stock Plans (ESPP/RSU) Tracking

**Status: ✅ Implemented**

## 1. Introduction

This document outlines the plan to add support for tracking Employee Stock Purchase Plans (ESPP) and Restricted Stock Units (RSU). Many users, especially in the tech industry, receive a significant portion of their compensation in this form. Accurately tracking these assets, including their unique cost basis and tax implications, is essential for a complete financial picture.

**User Story:** "As a user, I want to track my ESPP purchases and RSU vesting events, so I can accurately see their performance, cost basis, and manage my holdings within my portfolio."

## 2. Problem Description

Standard `BUY` and `SELL` transactions do not adequately capture the nuances of ESPP and RSU events:

1.  **RSU Vesting:** When RSUs vest, the employee acquires shares at a cost basis equal to the Fair Market Value (FMV) on the vest date, but the actual cash cost to the employee is $0. The current system requires a `price_per_unit > 0`, making it impossible to model this correctly.
2.  **ESPP Purchases:** ESPP purchases are bought at a discount to the market price, often based on a "lookback" period. Capturing details like the offering period, market price, and discount applied is crucial for understanding the true gain and for tax purposes (qualifying vs. disqualifying dispositions).
3.  **"Sell to Cover":** A common transaction associated with RSUs is automatically selling a portion of the vested shares to cover income taxes. This needs to be represented as a distinct `SELL` transaction that occurs immediately after the `RSU_VEST` event.

## 3. Proposed Solution

We will introduce new, specialized transaction types and enhance the system to store the necessary metadata for these events. The implementation will be phased to deliver value incrementally.

### 3.1. Phased Approach

*   **Phase 1: Backend Core Implementation.** Introduce database schema changes and update the backend API to support the new transaction types and their associated metadata.
*   **Phase 2: Frontend Manual Entry.** Develop the UI components (e.g., a new "Add Award" modal) to allow users to manually enter ESPP purchases and RSU vesting events.
*   **Phase 3 (Future):** Explore adding support for automated import from brokerage statements (e.g., E*TRADE, Fidelity, Schwab) that contain ESPP/RSU transaction data.

---

## 4. Technical Design & Architecture (Phase 1)

### 4.1. Database Schema Changes

We will extend the existing `transactions` table to accommodate the new data points without adding new tables, keeping the core logic centralized.

1.  **Update `TransactionType` Enum:**
    *   In `backend/app/schemas/enums.py`, add `ESPP_PURCHASE` and `RSU_VEST` to the `TransactionType` enum.

2.  **Extend `Transaction` Model:**
    *   In `backend/app/models/transaction.py`, add a new column to the `Transaction` model:
        *   `details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)` (Implemented as `details` to avoid conflict with SQLAlchemy `metadata`)

    *   This flexible `JSON` column will store the specific details for each award type.
    *   **`RSU_VEST` Metadata Schema:**
        ```json
        {
          "fmv": 150.25,
          "fx_rate": 83.50,
          "sell_to_cover": { ... }
        }
        ```
        *   The main `transaction.price_per_unit` will be set to `0.00` to reflect the user's cost.
        *   The `fmv` (Fair Market Value) will be stored in the metadata and used by the analytics engine to calculate performance.

    *   **`ESPP_PURCHASE` Metadata Schema:**
        ```json
        {
          "fmv": 160.50,
          "fx_rate": 83.50
        }
        ```
        *   The main `transaction.price_per_unit` will store the actual discounted price paid by the employee.
        *   The `fmv` (Market Price) is stored in the metadata for informational purposes.

### 4.2. API Endpoint Modifications

The existing transaction endpoints will be used, but the logic will be enhanced.

*   **`POST /api/v1/portfolios/{portfolio_id}/transactions`:**
    *   The request body (`TransactionCreate` schema) will be updated to accept the optional `details` dictionary.
    *   The backend logic will validate the `details` structure based on the provided `transaction_type`.
    *   **Response Change:** Now returns `{"created_transactions": [...]}` to support returning multiple transactions (e.g. RSU + Sell to Cover).

*   **`GET /api/v1/fx-rate?from=USD&to=INR&date=YYYY-MM-DD` (New Endpoint):**
    *   A new utility endpoint will be created to provide historical and current exchange rates. This will be used by the frontend to assist the user during manual entry.

---

## 5. Frontend Development Plan (Phase 2)
 
### 5.1. UI/UX Mock-up and Flow

#### On-the-Fly Asset Creation

The asset search component provides a robust, user-driven flow for creating new assets that don't yet exist in the local database. This prevents the system from being cluttered with incorrect assets due to typos.

1.  User types a ticker that does not exist (e.g., "ACME.L").
2.  The backend's `/lookup` endpoint searches for potential matches from external providers (like Yahoo Finance) and returns them to the frontend.
3.  If the user selects a search result, the frontend makes a second request to the backend to create a new, permanent asset record in the local database.
4.  If no results are found, the UI presents an option to **"Create Asset 'ACME.L'..."**, allowing the user to confirm the creation.
5.  The modal then proceeds with the newly created asset.

```
 +------------------------------------------------------+
 |  Asset:          [ ACME.L                     | v ]   |
 +------------------------------------------------------+
 | > Search results...                                  |
 | > Add new asset 'ACME.L'...      <-- User clicks this |
 +------------------------------------------------------+
```
 
To ensure clarity, the user journey for adding an ESPP or RSU award will be as follows:
 
#### Step 1: Initiate "Add Award"
 
The user navigates to their portfolio and clicks the "Add" button, which now presents a dropdown menu.
The user navigates to their portfolio. The "Add Transaction" button is a **split button**. The primary action (clicking the main button area) immediately opens the standard transaction modal. The dropdown reveals the new "Add ESPP/RSU Award" option. This keeps the most common workflow fast and intuitive.
 
```
 +-----------------------+
 | Add Transaction  | v  |
 +-----------------------+
 | Standard Transaction  |
 | Add ESPP/RSU Award    |  <-- User clicks this
 +-----------------------+
```
 
#### Step 2: The "Add Award" Modal (RSU Vest Example)
 
Clicking "Add ESPP/RSU Award" from the dropdown opens a new modal. The user selects "RSU Vest" and chooses an asset. The system dynamically adapts the currency fields based on the selected asset's country (e.g., USD for US stocks, EUR for German stocks). The FX rate is then fetched for the correct currency pair.
 
```
 +------------------------------------------------------+
 | Add ESPP/RSU Award                             [ X ] |
 +------------------------------------------------------+
 |                                                      |
 |  Award Type: [ (•) RSU Vest ] [ ( ) ESPP Purchase ]   |
 |                                                      |
 |  Asset:          [ Google (GOOGL)           | v ]   |
 |  Vest Date:      [ 2025-11-15               | 📅 ]   |
 |  Gross Qty Vested:[ 10.00000000                    ]   |
 |  FMV at Vest:    [ 150.25                       ] USD |
 |                                                      |
 |  ----------------- INR Conversion -----------------   |
 |  FX Rate (USD-INR): [ 83.50 (auto-fetched)         ]   |
 |  Taxable Income:   [ ₹1,25,458.75 (read-only)     ]   |
 |                                                      |
 |  [x] Record 'Sell to Cover' for taxes                |
 |  Shares Sold:    [ 4.00000000                     ]   |
 |  Sale Price:     [ 150.25 (defaults to FMV)     ] USD |
 |                                                      |
 |  -------------------- Summary --------------------   |
 |  Net Shares Received: [ 6.00000000 (read-only)     ]   |
 |                                                      |
 |                           +--------------------+     |
 |                           |     Add Award      |     |
 |                           +--------------------+     |
 +------------------------------------------------------+
 ```
 
 **Backend Logic:** When the user submits this form, the system will create **two** separate transactions:
 
 UI/UX Note: The Sale Price for the "Sell to Cover" transaction will automatically default to the value entered in FMV at Vest. The user can override this if their brokerage statement shows a slightly different sale price.
 
 1.  An `RSU_VEST` transaction for the **gross quantity** (10 shares) with a price of 0.
 2.  A `SELL` transaction for the **shares sold** (4 shares) at the specified sale price.  

#### Step 3: The "Add Award" Modal (ESPP Purchase Example)
 
If the user selects "ESPP Purchase", the form fields change accordingly.
 
```
 +------------------------------------------------------+
 | Add ESPP/RSU Award                             [ X ] |
 +------------------------------------------------------+
 |                                                      |
 |  Award Type: [ ( ) RSU Vest ] [ (•) ESPP Purchase ]   |
 |                                                      |
 |  Asset:          [ Microsoft (MSFT)         | v ]   |
 |  Purchase Date:  [ 2025-12-01               | 📅 ]   |
 |  Quantity:       [ 25.00000000                    ]   |
 |  Purchase Price: [ 340.00                       ] USD |
 |  Market Price:   [ 400.00                       ] USD |
 |                                                      |
 |  ----------------- INR Conversion -----------------   |
 |  FX Rate (USD-INR): [ 83.60 (auto-fetched)         ]   |
 |  Total Cost (INR):  [ ₹7,10,600.00 (read-only)     ]   |
 |                                                      |
 |                           +--------------------+     |
 |                           |     Add Award      |     |
 |                           +--------------------+     |
 +------------------------------------------------------+
 ```
 
#### Step 4: Displaying the New Transaction
 
After submission, the new transaction appears in the portfolio's transaction list. It is clearly labeled and has an icon to view the extra metadata.
 
```
 | Date       | Type         | Asset         | Qty | Price (USD) | Total (INR) |
 |------------|--------------|---------------|-----|-------------|-------------|
 | 2025-11-15 | [SELL]       | Google (GOOGL)| -4  | 150.25      | 50,183.50   |
 | 2025-11-15 | [RSU] Vest   | Google (GOOGL)| 10  | 0.00        | 0.00        | (i)
 | 2025-10-20 | [BUY]        | Reliance (REL)| 50  | 2,800.00    | 1,40,000.00 |
 ```
 
#### Step 5: Selling Acquired Shares

When a user sells shares acquired via ESPP/RSU, they will use the standard **"Add Transaction"** flow. The necessary currency conversion for these sales will be handled by the enhancements detailed in a separate feature plan for foreign stock transactions.

Hovering over the `(i)` info icon would show a tooltip with the metadata:
 
```
 +--------------------------------+
 | RSU Vest Details:              |
 |   FMV at Vest: $150.25         |
 |   FX Rate: 83.50               |
 |   Taxable Income: ₹1,25,458.75 |
 +--------------------------------+
 ```

## 6. Task Prioritization

This feature is a high priority for enhancing the application's value to a broad user base.
1.  **Task 1 (Backend):** Implement the database and API changes described in Section 4.
2.  **Task 2 (Frontend):** Implement the new "Add Award" modal and display logic as described in Section 5.
3.  **Task 3 (Documentation):** Update user guides to explain how to add and interpret ESPP/RSU transactions.

## 7. Testing Plan

### 7.1. Backend Unit & Integration Tests

*   **Test `RSU_VEST` Creation:** Verify that submitting an RSU form creates an `RSU_VEST` transaction with `price_per_unit = 0` and correct metadata.
*   **Test `ESPP_PURCHASE` Creation:** Verify that submitting an ESPP form creates an `ESPP_PURCHASE` transaction with the correct discounted `price_per_unit` and metadata.
*   **Test 'Sell to Cover' Logic:** Verify that when "Sell to Cover" is checked, the system creates two transactions: one `RSU_VEST` for the gross quantity and one `SELL` for the shares sold.
*   **Test Validation:** Test failure cases, such as missing metadata or incorrect price for an RSU vest.

### 7.2. Frontend Component Tests (`AddAwardModal.tsx`)

*   **Test Form Switching:** Verify that the modal correctly switches between the "RSU Vest" and "ESPP Purchase" forms.
*   **Test "Sell to Cover" Visibility:** Assert that the "Shares Sold" and "Sale Price" fields are only visible when the "Record 'Sell to Cover'" checkbox is checked.
*   **Test Read-Only Calculations:** Assert that fields like "Taxable Income" and "Net Shares Received" are calculated correctly and are read-only.
*   **Test API Integration:** Mock API calls to test that FX rates are fetched and that the correct payload is sent on submission.

### 7.3. End-to-End (E2E) Tests

*   **Full RSU Flow with Sell to Cover:**
    1.  Navigate to a portfolio and open the "Add ESPP/RSU Award" modal.
    2.  Fill out the RSU form, including the "Sell to Cover" section.
    3.  Submit the form and verify that two new transactions (`RSU_VEST` and `SELL`) appear in the history.
    4.  Verify that the consolidated holdings view shows the correct *net* quantity of shares.

*   **Full ESPP Flow:**
    1.  Open the "Add ESPP/RSU Award" modal.
    2.  Fill out and submit the ESPP purchase form.
    3.  Verify that a single `ESPP_PURCHASE` transaction appears in the history and that holdings are updated correctly.