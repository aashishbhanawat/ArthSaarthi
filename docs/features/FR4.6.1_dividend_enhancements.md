# FR4.6.1: Dividend Enhancements (Stock DRIP & Currency)

**Status: 🚧 In Progress**

> **Implementation Notes (December 2024):**
> - Frontend implementation complete for domestic Stock DRIP
> - Editable FX rate for foreign dividends implemented
> - E2E tests added for Stock DRIP flow
> - See PR: `feat/FR4.6.1-dividend-enhancements`

## 1. Introduction

This document outlines enhancements to the existing dividend tracking functionality. This plan introduces two key improvements:

1.  **Dividend Reinvestment Plan (DRIP) for Stocks:** Adding a clear workflow for handling stock dividends that are automatically reinvested.
2.  **Currency Conversion for Foreign Dividends:** Adding support for correctly logging dividends received in a foreign currency (e.g., USD), including for reinvestment scenarios.

This plan will adopt the standards established in `FR8.1.1` for handling foreign currency and transaction metadata.

## 2. Dividend Reinvestment Plan (DRIP) for Domestic Stocks

### Problem
The current implementation for stock dividends only logs a single `DIVIDEND` transaction. It does not have a clear flow for handling dividends that are automatically reinvested to purchase more shares.

### Solution
We will update the "Dividend" form for stocks to mirror the robust two-transaction logic used for mutual funds.

*   **UI Change:** The form will include a **"Reinvest Dividend?"** checkbox. If checked, a "Reinvestment Price" field will appear.
*   **Frontend Logic:** When submitted, the frontend will create **two** transactions:
    1.  A `DIVIDEND` transaction to record the cash income, correctly impacting Realized P&L.
    2.  A `BUY` transaction to record the purchase of new shares. The quantity for this `BUY` will be calculated as `Total Dividend Amount / Reinvestment Price`.

#### Mockup: Domestic Stock Dividend with Reinvestment

```text
│  Action Type: [ Dividend ▼ ]                           │
│                                                          │
│  Payment Date:     [ 2025-12-01   ]                       │
│  Total Amount:     [ 1500.00      ] INR                  │
│  [x] Reinvest Dividend                                   │
│  Reinvestment Price: [ 2500.00      ]                       │
│  (New shares to be added: 0.60) (read-only)              │
│                                     [ Cancel ] [ Save ]  │
```

## 3. Currency Conversion for Foreign Dividends (Cash Payout)

### Problem
The system currently assumes all dividends are paid in INR. It cannot accurately record a dividend paid in USD for a US-listed stock.

### Solution
We will enhance the dividend form to handle foreign currencies, making the auto-fetched FX rate editable to match broker statements.

*   **UI Change:** When adding a dividend for a foreign asset, the form will show an "INR Conversion" section.
*   **Backend Logic:** The `fx_rate` will be stored in the `details` field of the `DIVIDEND` transaction. The transaction's `price_per_unit` will be `1`, and `quantity` will store the dividend amount in the foreign currency.

#### Mockup: Foreign Stock Dividend (Cash)

```text
│  Action Type: [ Dividend ▼ ]                             │
│                                                          │
│  Asset: [ Google (GOOGL) ▼ ]                             │
│  Payment Date:     [ 2025-12-01   ]                      │
│  Total Amount:     [ 20.00        ] USD                  │
│                                                          │
│  ----------------- INR Conversion -----------------      │
│  FX Rate (USD-INR): [ 83.50 (auto-fetched)         ]     │  <-- User can edit
│  Value (INR):      [ ₹1,670.00    ] (read-only)          │
│                                     [ Cancel ] [ Save ]  │
```

## 4. Combined Scenario: DRIP for Foreign Dividends

### Problem
Brokerage statements for foreign DRIPs can vary. Some show the reinvestment price, while others only show the number of new shares credited. The system needs to be flexible enough to handle both data entry methods.

### Solution
The UI will combine all necessary fields and allow the user to enter the information they have, calculating the rest.

*   **UI Change:** For a foreign dividend, checking "Reinvest Dividend" will reveal a section where the user can input **either** the reinvestment price **or** the quantity of new shares. The other field will be calculated automatically. The FX rate remains editable.
*   **Frontend Logic:** When submitted, the frontend will create two transactions, both with the same `exchange_rate_to_inr` in their metadata:
    1.  A `DIVIDEND` transaction for the cash income.
    2.  A `BUY` transaction for the new shares, using the foreign currency price and quantity.

#### Mockup: Foreign Stock Dividend with Reinvestment

```text
│  Action Type: [ Dividend ▼ ]                             │
│                                                          │
│  Asset: [ Google (GOOGL) ▼ ]                             │
│  Payment Date:     [ 2025-12-01   ]                      │
│  Total Amount:     [ 20.00        ] USD                  │
│                                                          │
│  ----------------- INR Conversion -----------------      │
│  FX Rate (USD-INR): [ 83.50 (auto) ]  <-- User can edit
│  Value (INR):      [ ₹1,670.00    ] (read-only)          │
│                                                          │
│  [x] Reinvest Dividend                                   │
│  ---------------- Reinvestment Details --------------    │
│  (Enter either Price or New Shares)                      │
│                                                          │
│  Reinvestment Price: [ 180.00       ] USD                │
│  New Shares Received: [ 0.11111111   ] (read-only)       │
│                                                          │
│                                     [ Cancel ] [ Save ]  │
```

## 5. Testing Plan

### 5.1. Backend Unit & Integration Tests

*   **Test Stock DRIP:** Verify that a DRIP event correctly creates both a `DIVIDEND` and a `BUY` transaction and that holdings are updated correctly.
*   **Test Foreign Dividend (Cash):** Verify a `DIVIDEND` transaction for a USD asset correctly stores the `exchange_rate_to_inr` in its metadata and that Realized P&L is calculated in INR.
*   **Test Foreign Dividend (DRIP):** Verify that a foreign DRIP event creates two transactions (`DIVIDEND` and `BUY`), both with the correct `exchange_rate_to_inr` in their metadata.

### 5.2. Frontend Component Tests (`TransactionFormModal.tsx`)

*   **Test Domestic DRIP UI:** Assert that checking "Reinvest Dividend" for an INR stock shows the "Reinvestment Price" field.
*   **Test Foreign Dividend UI:** Assert that the "INR Conversion" section is visible for foreign stocks and that the FX rate is editable.
*   **Test Foreign DRIP UI Flexibility:**
    1.  When entering "Reinvestment Price", assert that "New Shares Received" is calculated and read-only.
    2.  When entering "New Shares Received", assert that "Reinvestment Price" is calculated and read-only.

### 5.3. End-to-End (E2E) Tests

*   **Full Stock DRIP Flow (Domestic):**
    1.  Log a dividend for an INR stock, check "Reinvest Dividend", and submit.
    2.  Verify two transactions appear and the holding quantity has increased.
*   **Full Foreign Dividend Flow (DRIP):**
    1.  Log a dividend for a USD stock, check "Reinvest Dividend", and fill in the reinvestment details.
    2.  Edit the auto-fetched FX rate.
    3.  Submit and verify two transactions appear, both reflecting the correct foreign currency details and the user-provided FX rate.