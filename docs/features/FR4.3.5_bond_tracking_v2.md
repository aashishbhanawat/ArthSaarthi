# Feature Plan (v2): Bond & T-Bill Tracking

**Status: ✅ Done (including Coupon Tracking)**
**Feature ID:** FR4.3.5
**Title:** Implement Flexible Tracking for Bonds (Corporate, Govt, SGBs, T-Bills)
**User Story:** As an investor in fixed-income securities, I want to track my various types of bonds (Corporate, Government, SGBs, T-Bills), so that I can accurately monitor their market value, coupon payments, and overall contribution to my portfolio.

---

## 1. Implementation Progress

*   [x] **Phase 1: Backend Implementation:** Create the database model, Pydantic schemas, CRUD logic, and API endpoints for creating and managing bonds.
*   [x] **Phase 2: Frontend Data Layer:** Create TypeScript types (`bond.ts`), API service functions (`bondApi.ts`), and React Query hooks (`useBonds.ts`).
*   [x] **Phase 3: Frontend UI - Add Transaction:** Update the `TransactionFormModal` to include the "Bond" asset type and the detailed form for capturing bond attributes as per the mockups.
*   [x] **Phase 4: Frontend UI - Display & Details:** Implement the `BondHoldingRow` for the main holdings table and create the `BondDetailModal` for the drill-down view.
*   [x] **Phase 5: E2E Testing:** Create an end-to-end test to validate the full user flow of adding and tracking a bond.

---

## 1. Objective

The initial Bond tracking implementation was too rigid, using only a simplified book value for valuation. This plan details a full revamp to support a wide range of fixed-income securities (Corporate Bonds, Government Bonds, SGBs, T-Bills) with a flexible, multi-tiered valuation strategy. The goal is to prioritize live market prices where available, use appropriate fallback logic (e.g., gold price for SGBs), and introduce a framework for tracking coupon payments.

---

## 2. UI/UX Requirements

### 2.1. Adding a Bond: User Flows & UI

There are two primary scenarios for adding a bond transaction:
1.  The bond is not yet known to the system (user-defined).
2.  The bond exists in the master asset list (pre-seeded), but the user is adding it to their portfolio for the first time.

In both cases, the goal is to capture both the bond's specific attributes and the details of the first `BUY` transaction in a single, seamless modal flow.

#### 2.1.1. Flow 1: Adding a New, User-Defined Bond

This flow is used when the user searches for a bond and it is not found in the master asset list.

1.  User clicks "Add Transaction".
2.  They select "Bond" as the asset type.
3.  They search for the bond name/ISIN. If not found, they can proceed to create a new one.
4.  The "Add Bond" form appears, requiring the user to fill in all details.

**Mockup: "Add New Bond" Form**
```text
┌──────────────────────────────────────────────────────────┐
│ Add Transaction                                       [X]│
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Asset Type: [ Bond ▼ ]                                  │
│  Search/Name: [ NHAI N2 8.3% 2027 (Create New) ▼ ]       │
│                                                          │
│  ┌─ Bond Details ───────────────────────────────────────┐  │
│  │                                                      │  │
│  │  Bond Type                        ISIN (Optional)     │  │
│  │  [ Corporate ▼ ]                  [ INE906B07CB9 ]    │  │
│  │                                                      │  │
│  │  Coupon Rate (%)    Face Value      Maturity Date     │  │
│  │  [ 8.30      ]      [ 1000 ]        [ 2027-01-25 ]    │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─ Your First Purchase (BUY Transaction) ──────────────┐  │
│  │                                                      │  │
│  │  Quantity             Price per Unit    Date          │  │
│  │  [ 100          ]     [ 1015.50    ]    [ 2024-05-10 ]│  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                          │
│                                     [ Cancel ] [ Save ]  │
└──────────────────────────────────────────────────────────┘
```
*   **Dynamic Fields:** The form will adapt based on the `Bond Type` selected. For example, if `TBILL` is chosen, the `Coupon Rate` field will be disabled and set to 0.

#### 2.1.2. Flow 2: Adding a Pre-Seeded Bond

The asset seeder populates the database with thousands of bonds with basic details (Name, ISIN). This flow handles when a user adds a transaction for one of these for the first time.

1.  User clicks "Add Transaction" and selects "Bond".
2.  They search for the bond by ISIN or name (e.g., `INE906B07CB9`).
3.  The system finds the pre-seeded asset. Since this is the first time the user is adding it, the system prompts them to enrich the asset with the missing bond-specific details.

**Mockup: Enriching a Pre-Seeded Bond**

```text
┌──────────────────────────────────────────────────────────┐
│ Add Transaction                                       [X]│
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Asset Type: [ Bond ▼ ]                                  │
│  Search/Name: [ NHAI N2 8.3% 2027 (INE906B07CB9) ▼ ]     │
│                                                          │
│  ┌─ Confirm Bond Details (Enriching Asset) ─────────────┐  │
│  │                                                      │  │
│  │  Bond Type                        ISIN (from search)  │  │
│  │  [ Corporate ▼ ]                  [ INE906B07CB9 ]    │  │
│  │                                                      │  │
│  │  Coupon Rate (%)    Face Value      Maturity Date     │  │
│  │  [ 8.30      ]      [ 1000 ]        [ 2027-01-25 ]    │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─ Your First Purchase (BUY Transaction) ──────────────┐  │
│  │                                                      │  │
│  │  Quantity             Price per Unit    Date          │  │
│  │  [ 100          ]     [ 1015.50    ]    [ 2024-05-10 ]│  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                          │
│                                     [ Cancel ] [ Save ]  │
└──────────────────────────────────────────────────────────┘
```

#### 2.1.3. Form Variations by Bond Type

The "Bond Details" section of the form will dynamically adapt based on the selected `Bond Type` to ensure correct data capture.

*   **For Sovereign Gold Bonds (SGBs):**
    *   `Bond Type` is `SGB`.
    *   The `Quantity` label in the purchase section changes to `Quantity (grams)`.
    *   `Face Value` field is hidden/disabled as it's not relevant.
    *   `Coupon Rate` is pre-filled and read-only to `2.50%` (the standard RBI rate for SGBs).
*   **For Treasury Bills (T-Bills):**
    *   `Bond Type` is `TBILL`.
    *   `Coupon Rate` field is disabled and set to `0.00%`, as T-Bills are zero-coupon instruments.
    *   The user enters the `Face Value` (e.g., 100) and the discounted `Price per Unit` they paid (e.g., 98.50).

#### 2.1.4. Flow 3: Selling or Adding to an Existing Bond

This flow is used when a user wants to log a `SELL` transaction or an additional `BUY` for a bond they already own.

1.  User clicks "Add Transaction".
2.  They select "Bond" as the asset type.
3.  They search for and select an existing bond from their portfolio.
4.  A new "Transaction Type" dropdown appears, allowing them to choose `BUY`, `SELL`, or `COUPON`.

**Mockup: "Sell Bond" Form**
```text
┌──────────────────────────────────────────────────────────┐
│ Add Transaction for "NHAI N2 8.3% 2027"                 [X]│
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Asset Type:       [ Bond ▼ ] (Read-only)                │
│  Asset:             [ NHAI N2 8.3% 2027 ▼ ] (Read-only)   │
│  Transaction Type: [ SELL ▼ ]                            │
│                    (Options: Buy, Sell, Coupon)            │
│                                                          │
│  Quantity             Price per Unit    Date             │
│  [ 50           ]     [ 1025.00    ]    [ 2024-08-01 ]   │
│                                                          │
│                                     [ Cancel ] [ Save ]  │
└──────────────────────────────────────────────────────────┘
```


### 2.2. Holdings Table View

Once added, the bond will appear in the "Fixed Income" section of the main holdings table.

**Mockup: "Fixed Income" Section**
```text
▼ Fixed Income (1)
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ Asset           | Type      | Coupon | Maturity   | Invested    | Current Value | Actions │
├─────────────────┼───────────┼────────┼────────────┼─────────────┼───────────────┼─────────┤
│ NHAI N2 8.3% 27 | BOND      | 8.30%  | 2027-01-25 | ₹1,01,550   | ₹1,05,300     | [⚙]     │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3. Bond Detail (Drill-Down) View

Clicking on a bond row in the holdings table will open the `BondDetailModal.tsx`, providing a comprehensive overview.

**Mockup: `BondDetailModal.tsx`**
```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Bond: NHAI N2 8.3% 2027                                                             [X]│
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  ┌─ Details ───────────┬─ Valuation ───────────┬─ Analytics ──────────┐            │
│  │ ISIN: INE906B07CB9   │ Current Value: 105,300 │ Annualized (XIRR): 9.15% │            │
│  │ Maturity: 2027-01-25 │ Invested:    101,550   │                          │            │
│  │ Coupon: 8.30%        │ Unrealized:  +3,750    │                          │            │
│  └──────────────────────┴────────────────────────┴────────────────────────┘            │
│                                                                                        │
│  Transaction History                                                                   │
│ ┌──────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ Date        | Description              | Quantity | Price   | Amount        | Actions │ │
│ ├─────────────┼──────────────────────────┼──────────┼─────────┼───────────────┼─────────┤ │
│ │ 15 Jul 2024 | Coupon Payment           | -        | -       | + ₹4,150.00   | [⚙]     │ │
│ │ 10 May 2024 | Buy                      | 100      | 1015.50 | - ₹1,01,550.00| [⚙]     │ │
│ └──────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```
---

## 4. Backend Requirements

### 4.1. Database Schema Changes (`models.Bond`)

A new `bonds` table will be created to store the unique attributes of each bond, linked to the main `assets` table.

| Column Name      | Data Type | Constraints                               | Description                                                               |
| :--------------- | :-------- | :---------------------------------------- | :------------------------------------------------------------------------ |
| `id`             | `UUID`    | `PRIMARY KEY`                             | Unique identifier for the bond record.                                    |
| `asset_id`       | `UUID`    | `FOREIGN KEY (assets.id)`, `NOT NULL`     | Links to the main asset record.                                           |
| `bond_type`      | `String`  | `NOT NULL`                                | Enum: `CORPORATE`, `GOVERNMENT`, `SGB`, `TBILL`.                          |
| `face_value`     | `Numeric` | `NULLABLE`                                | The face value of the bond (e.g., 1000). Null for SGBs.                   |
| `coupon_rate`    | `Numeric` | `NULLABLE`                                | The annual coupon rate (e.g., 7.5 for 7.5%). Null for T-Bills.            |
| `maturity_date`  | `Date`    | `NOT NULL`                                | The date the bond matures.                                                |
| `isin`           | `String`  | `NULLABLE`, `INDEX`                       | ISIN for market price lookups of tradable bonds.                          |
| `payment_frequency`| `String`  | `NULLABLE`                                | Enum: `ANNUALLY`, `SEMI_ANNUALLY`, `QUARTERLY`, `MONTHLY`. For auto-coupon. |
| `first_payment_date`| `Date`    | `NULLABLE`                                | The date of the first coupon payment. For auto-coupon.                    |

### 4.2. Valuation Logic (`crud_holding.py`)
The valuation logic for bonds will be updated to a robust, multi-step fallback strategy based on `bond_type`. This requires a refactor of the `FinancialDataService`.

#### 4.2.1. `FinancialDataService` Refactor
The service will be refactored to support multiple data providers for different asset classes. A new, dedicated bond pricing provider (e.g., from a source like `SEBI` or a commercial data vendor) will be integrated.

#### 4.2.2. Fallback Strategy
The `crud_holding.py` logic will be updated to use the following fallback chain for valuation:
1.  **Primary Source (New Bond API):** For any bond with an ISIN, attempt to fetch a live market price from the new, dedicated bond pricing provider. This is the preferred method.
2.  **Secondary Source (`yfinance`):** If the primary source fails, attempt to fetch a price from `yfinance` using the ticker symbol. This is a best-effort secondary source. **Note:** This was found to be unreliable for most Indian bonds.
4.  **Accretion Fallback (T-Bills):** For T-Bills, which are zero-coupon, the value will be calculated based on time-based accretion from the purchase price towards the face value at maturity.
5.  **Final Fallback (Book Value):** If all other methods fail for any bond type, the system will value the holding at its book value (average cost basis). This ensures that the asset is never valued at zero.

### 4.3. API Endpoints

New endpoints will be added for full CRUD operations on bonds.

*   `POST /api/v1/portfolios/{portfolio_id}/bonds/`: Create a new bond asset and its first transaction.
*   `GET /api/v1/portfolios/{portfolio_id}/bonds/{bond_id}`: Get details for a single bond.
*   `PUT /api/v1/portfolios/{portfolio_id}/bonds/{bond_id}`: Update a bond's details.
*   `DELETE /api/v1/portfolios/{portfolio_id}/bonds/{bond_id}`: Delete a bond.
*   `GET /api/v1/portfolios/{portfolio_id}/bonds/{bond_id}/analytics`: Get XIRR analytics for a single bond.

### 4.4. Asset Seeding (`cli.py`)

The asset seeder script will be enhanced to correctly identify and categorize different bond types from the master data file. The `_map_series_to_asset_type` function will be updated to return a specific `bond_type` based on the series code (e.g., `GB` -> `SGB`, `GS` -> `GOVERNMENT`, `TB` -> `TBILL`, `N*`/`Y*` -> `CORPORATE`).

### 4.5. Coupon Payment Handling

Coupon payments will be handled in two phases to provide immediate functionality while planning for future automation.

*   **Phase 1 (Manual Entry):**
    *   A new `TransactionType` of `COUPON` will be added.
    *   **Status: ✅ Done**
    *   Users will manually create a `COUPON` transaction to record interest payments received from their bonds.
    *   This ensures that all cash flows are accurately captured for XIRR and Realized P&L calculations. This approach is consistent with the initial plan for handling dividends (FR4.5).

*   **Phase 2 (Automated Generation - Future Enhancement):**
    *   A background job or on-demand service will be implemented.
    *   This service will scan for bond holdings and automatically generate the `COUPON` transactions based on the bond's `coupon_rate` and a predefined payment frequency (e.g., semi-annually).
    *   This will reduce manual data entry and improve accuracy for standard fixed-rate bonds.

*   **Implementation Complexity & Challenges:**
    *   **Data Requirements:** This feature is highly dependent on having accurate `payment_frequency` and `first_payment_date` data for each bond. The UI for adding/editing bonds must be updated to capture this information.
    *   **Background Task Scheduler:** A reliable background job scheduler (e.g., `apscheduler` or Celery) would need to be integrated into the backend architecture to run daily checks for due coupon payments.
    *   **Idempotency:** The background job must be idempotent, meaning it cannot create duplicate `COUPON` transactions if it is run multiple times for the same day (e.g., after a server restart).
    *   **Handling Edge Cases:** The logic must correctly handle various bond types. For example, it should ignore zero-coupon bonds (`TBILL`) and would require a separate, more complex implementation for floating-rate bonds.
    *   **Editing & Deletion:** If a user edits a bond's core details (e.g., `coupon_rate`, `maturity_date`), the system would need logic to find and either delete or update all future, auto-generated coupon transactions.


### 4.6. Analytics Engine Updates (`crud_analytics.py`)

To ensure accurate performance measurement, the analytics engine must be updated to recognize and correctly process cash flows from bonds, specifically coupon payments.

*   **Portfolio-Level Analytics (`get_portfolio_analytics`):**
    *   The main portfolio XIRR calculation must be updated to include `COUPON` transactions as positive cash inflows. The coupon amount will be stored in the `quantity` field of the transaction.

*   **Asset-Level Analytics (`get_asset_analytics`):**
    *   The XIRR calculation for a single bond asset must also be updated.
    *   Coupon payments associated with the asset should be treated as positive cash inflows when calculating both realized and unrealized XIRR for that specific bond.


## 5. Frontend Implementation Plan

*   **Types:** Create `frontend/src/types/bond.ts`.
*   **API Service:** Update `frontend/src/services/portfolioApi.ts` with functions for bond CRUD.
*   **Hooks:** Create `frontend/src/hooks/useBonds.ts` for React Query hooks.
*   **UI Components:**
    *   Update `TransactionFormModal.tsx` to include a form for adding bonds.
    *   Create a new `BondDetailModal.tsx` for the drill-down view.
    *   Create a new `BondHoldingRow.tsx` for the sectioned holdings table.
*   **State Management & Cache Invalidation:**
    *   The `useBonds.ts` hook will contain mutations for creating, updating, and deleting bonds and their associated transactions.
    *   On successful mutation (`onSuccess`), these hooks must invalidate all relevant React Query keys to ensure the UI updates automatically. This includes:
        *   `['portfolioHoldings', portfolioId]`: To refresh the main holdings table and update metrics like Current Value and Invested Amount.
        *   `['portfolioSummary', portfolioId]`: To update the portfolio-level summary metrics.
        *   `['bondAnalytics', bondId]`: To recalculate and refresh the XIRR in the `BondDetailModal`.
        *   `['portfolioAnalytics', portfolioId]`: To update the overall portfolio XIRR.


## 6. Testing Plan

*   **Backend Unit Tests:**
    *   Write valuation tests for each bond type (Corporate, Government, SGB, T-Bill).
    *   Create specific tests for each step of the valuation fallback strategy:
        *   Primary API price fetch.
        *   `yfinance` fallback.
        *   SGB valuation via gold price.
        *   T-Bill valuation via accretion model.
        *   Book value as the final fallback.
    *   Test XIRR calculation with and without `COUPON` transactions.

*   **Frontend Component Tests:**
    *   Write unit tests for the `BondDetailModal` to ensure all data points are displayed correctly.
    *   Write unit tests for the `BondHoldingRow` component.
    *   Test the dynamic form variations in `TransactionFormModal` for SGBs and T-Bills.

*   **E2E (End-to-End) Tests:**
    1.  **Full Lifecycle (Tradable Bond):**
        *   Create a new user-defined Corporate bond.
        *   Verify it appears correctly in the holdings table.
        *   Add a manual `COUPON` transaction for this bond.
        *   Open the detail modal and verify that the transaction history, valuation, and XIRR are correct.
        *   Sell a partial quantity of the bond.
        *   Verify holdings and analytics are updated correctly.
        *   Delete the bond holding and confirm it is removed from the portfolio.
    2.  **SGB (Sovereign Gold Bond) Flow:**
        *   Add a transaction for a pre-seeded SGB.
        *   Verify the form correctly shows `Quantity (grams)` and a read-only `2.50%` coupon rate.
        *   Verify its valuation is correctly calculated based on a mocked gold price.
    3.  **T-Bill (Treasury Bill) Flow:**
        *   Add a transaction for a T-Bill.
        *   Verify the form correctly shows a disabled `Coupon Rate` of `0.00%`.
        *   Verify its valuation is calculated using the accretion model (time-based value increase towards face value).
    4.  **Valuation Fallback (Book Value):**
        *   Create a bond with no ISIN or valid ticker.
        *   Verify that all market price fetches fail and the bond's current value defaults to its book value (invested amount).
