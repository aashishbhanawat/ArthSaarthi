---
name: '🚀 Feature Request'
about: 'Implement tracking for Bonds (Corporate, Govt, SGBs, T-Bills)'
title: 'feat: Implement tracking for Bonds (Corporate, Govt, SGBs, T-Bills)'
labels: 'enhancement, feature, epic:advanced-assets'
assignees: ''
---

### 1. User Story

**As an** investor in fixed-income securities,
**I want to** track my various types of bonds (Corporate, Government, SGBs, T-Bills),
**so that** I can accurately monitor their market value, coupon payments, and overall contribution to my portfolio.

---

### 2. Functional Requirements

*   [ ] Users must be able to add a new Bond asset.
*   [ ] The system must capture key bond details: ISIN, Bond Name, Bond Type (e.g., `CORPORATE`, `GOVERNMENT`, `SGB`, `TBILL`), Purchase Price, Face Value, Coupon Rate, Maturity Date, and Quantity.
*   [ ] The valuation logic must be flexible based on the bond type:
    *   For traded bonds with an ISIN, the system should fetch and use the live market price.
    *   For Sovereign Gold Bonds (SGBs), the system should use the current price of gold.
    *   For non-traded bonds, the system should calculate the value based on book value plus accrued interest.
*   [ ] Bonds must be displayed correctly in a dedicated "Fixed Income" section of the holdings table.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given I add a new tradable corporate bond with a valid ISIN, when I view my holdings, then its current value should reflect the latest market price.
*   [ ] **Scenario 2:** Given I add a Sovereign Gold Bond, when the price of gold changes, then the current value of my SGB holding should update accordingly.

---

### 4. Dependencies

*   This feature depends on the financial data API integration (`FR5.1`) to provide market prices for traded bonds and gold.

---

### 5. Additional Context

*   **Requirement ID:** `(FR4.3)`
*   This is a key part of the "Advanced Asset Support" epic and aligns with the v2 feature plan. It requires a more flexible backend model than the initial MVP.

