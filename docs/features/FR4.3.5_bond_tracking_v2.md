# Feature Plan (v2): Bond & T-Bill Tracking

**Status: 📝 Planned**
---
**Feature ID:** FR4.3.5
**Title:** Implement Flexible Tracking for Bonds (Corporate, Govt, SGBs, T-Bills)
**User Story:** As an investor in fixed-income securities, I want to track my various types of bonds (Corporate, Government, SGBs, T-Bills), so that I can accurately monitor their market value, coupon payments, and overall contribution to my portfolio.

---

## 1. Objective

The initial Bond tracking implementation was too rigid, using a simplified book value for valuation. This plan details a full revamp to support various bond types with more accurate, market-linked valuation strategies.

---

## 2. UI/UX Requirements

*   **Sectioned View:** Bonds will be displayed within the new "Fixed Income" collapsible section in the main holdings table.
*   **Dedicated Columns:** The "Fixed Income" section will have columns relevant to Bonds:
    *   **Columns:** Asset, Type (Bond), Coupon Rate, Maturity Date, Invested Amount, Current Value.
*   **Add Asset Flow:** The "Add Bond" form will be updated to include the new `bond_type` and `isin` fields.

---

## 3. Backend Requirements

### 3.1. Database Schema Changes (`models.Bond`)

The `Bond` model will be updated to be more flexible:
*   Add `bond_type`: Enum (`CORPORATE`, `GOVERNMENT`, `SGB`, `TBILL`).
*   Make `face_value` nullable, as it's not applicable for all types (e.g., SGBs are tracked in grams).
*   Add `isin`: String (Indexed, for market price lookups).

### 3.2. Valuation Logic (`crud_holding.py`)

The valuation logic for bonds will be updated to a multi-step strategy based on `bond_type`:
1.  **Tradable Bonds:** If a bond has an `isin` and `bond_type` is `CORPORATE` or `GOVERNMENT`, the `FinancialDataService` will attempt to fetch a live market price. `Current Value = Market Price * Quantity`.
2.  **Sovereign Gold Bonds (SGBs):** If `bond_type` is `SGB`, the `FinancialDataService` will fetch the current price of Gold. `Current Value = Gold Price * Quantity (in grams)`.
3.  **T-Bills & Zero Coupon:** If `bond_type` is `TBILL`, the valuation will be based on time-based accretion towards face value.
4.  **Fallback (Non-Traded):** If no market price is available, the system will fall back to calculating value based on book value plus accrued interest.

---

## 4. Testing Plan

*   **Backend Unit Tests:** Write new valuation tests for each bond type (tradable, SGB, non-traded fallback). Mock the `FinancialDataService` to return predictable prices.
*   **E2E Tests:**
    1. Create a tradable bond and verify its value is updated based on a mock market price.
    2. Create an SGB and verify its value is updated based on a mock gold price.
    3. Verify the bond appears correctly in the "Fixed Income" section of the holdings table.

