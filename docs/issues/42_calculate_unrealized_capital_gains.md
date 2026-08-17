---
name: '🚀 Feature Request'
about: 'Calculate and display unrealized capital gains and Section 112A exemption pooling'
title: 'feat: Calculate & Display Unrealized Capital Gains & Exemption Pooling (FR6.5 Phase 2)'
labels: 'enhancement, feature, epic:tax-readiness'
assignees: ''
---

**Release: v1.4.0 (Tax Readiness & Full Financial Picture)**
**GitHub Issue:** #516

### 1. User Story

**As an** investor using ArthSaarthi,  
**I want to** calculate and view my unrealized capital gains (STCG/LTCG) along with Section 112A equity exemption pooling,  
**so that** I can evaluate potential tax liabilities, optimize profit-booking, and plan tax-loss harvesting.

---

### 2. Functional Requirements

*   [ ] Calculate lot-level and holding-level unrealized Short-Term Capital Gains (STCG) and Long-Term Capital Gains (LTCG) using current market prices.
*   [ ] Categorize unrealized gains according to holding periods (Equity > 12 months = LTCG, Debt > 24 months = LTCG / post-April 2023 rules).
*   [ ] Implement Section 112A LTCG exemption pooling (statutory ₹1,25,000 threshold per financial year) across equity holdings to show remaining tax-free headroom.
*   [ ] Add unrealized tax liability projections to the Capital Gains page and Holdings detail views.
*   [ ] Provide API endpoint `GET /api/v1/tax/unrealized-gains` with portfolio and financial year filtering.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1 (Unrealized Holding LTCG/STCG Breakdown):** Given active equity holdings, when the user opens the Unrealized Capital Gains view, each holding displays quantity, cost basis, current market value, unrealized gain/loss, holding period, and tax classification (STCG vs LTCG).
*   [ ] **Scenario 2 (Section 112A Exemption Pooling):** Given ₹2,00,000 of total unrealized equity LTCG across portfolios, the system applies the ₹1.25L exemption threshold, displaying ₹1.25L exempt gains and ₹75,000 estimated taxable LTCG (taxed at 12.5%).
*   [ ] **Scenario 3 (Privacy Mode):** Under Privacy Mode, all monetary amounts in the unrealized capital gains UI are masked appropriately (`***`).

---

### 4. Dependencies

*   Depends on existing Tax Lot Accounting (FR4.4.3) and Realized Capital Gains Engine (FR6.5).
*   Depends on live price enrichment service (`FinancialDataService`).

---

### 5. Additional Context

*   **Requirement ID:** `(FR6.5 Phase 2 / FR6.5.7)`
*   This is part of Release v1.4.0 (Tax Readiness & Full Financial Picture).
