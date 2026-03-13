# FR6.6: Dividend Reporting - Detailed Requirements

**Version:** 1.0  
**Date:** 2026-03-13  
**Target Release:** v1.2.0

---

## 1. Overview

The Dividend Report feature enables users to export a structured report of all dividends received within a specific Financial Year (FY) for tax filing purposes, completing the tax reporting suite alongside Capital Gains (FR6.5).

---

## 2. Functional Requirements

### FR6.6.1: API Endpoint
**FR6.6.1.1:** The backend must provide an endpoint (e.g., `/api/v1/transactions/export/dividends` or via a new `reports` router) to export all transactions of type `DIVIDEND`.
**FR6.6.1.2:** The endpoint must accept filters for:
- Financial Year (`fy`) e.g., "2025-26"
- Portfolio ID (`portfolio_id`) - Optional, applies to all portfolios if not provided.

### FR6.6.2: Export Format
**FR6.6.2.1:** The export must be in CSV format.
**FR6.6.2.2:** The CSV must contain the following columns:
- Asset Name
- Ticker/Symbol
- Date (of dividend transaction)
- Quantity (shares/units held)
- Amount (total dividend received)
- Currency

### FR6.6.3: Foreign Dividends & Currency Conversion (Rule 115)
**FR6.6.3.1:** For dividends received from foreign assets (e.g., US ESPP/RSU), the report must list the dividend in its native currency (e.g., USD).
**FR6.6.3.2:** In accordance with Indian Income Tax provisions (Rule 115), the system should document the INR equivalent. 
**FR6.6.3.3:** The conversion rate to be applied is the State Bank of India (SBI) Telegraphic Transfer Buying Rate (TTBR) on the *last day of the month immediately preceding the month* in which the dividend is declared, distributed, or paid.
**FR6.6.3.4:** If automated fetching of historical SBI TTBR is not feasible (as it often requires a paid API or manual scraping), the system must:
- Either calculate a proxy rate using the available FX rate provider (e.g., `yfinance`) for that specific date (last day of previous month).
- OR provide the native currency amount and explicitly note the Rule 115 TTBR requirement in the exported report so the user/CA can apply the correct manual rate.
- In v1.2.0, providing the native amount with a proxy `yfinance` INR conversion and a disclaimer is acceptable.

### FR6.6.4: Frontend Integration
**FR6.6.3.1:** The application must present a unified location for tax reports. The "Capital Gains" page should be renamed or repurposed to "Tax Reports" or simply have a new "Export Dividend Report" button added to the existing Capital Gains UI or Transactions UI. (Proposed: Add an "Export Dividends (CSV)" button next to the "Export Gains (CSV)" button on the Capital Gains page).

---

## 3. Technical Dependencies
- Existing `Transaction` model and `transaction_type == DIVIDEND`.
- Existing utility functions to calculate FY date bounds.

## 4. Acceptance Criteria
- [ ] Users can export a CSV of dividends for a specific FY.
- [ ] Only transactions with type `DIVIDEND` are included.
- [ ] The generated CSV aligns with Indian tax reporting needs (informational summary).
