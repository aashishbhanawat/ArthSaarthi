---
name: '🚀 Feature Request'
about: 'feat: Implement Intra-Head Capital Loss Set-Off, Carry-Forward Loss Ledger & Tax-Loss Harvesting (FR6.5 Phase 3)'
title: 'feat: Implement Intra-Head Capital Loss Set-Off, Carry-Forward Loss Ledger & Tax-Loss Harvesting (FR6.5 Phase 3)'
labels: 'enhancement, feature, tax, backend, frontend'
assignees: ''
---

### 1. User Story

**As a** tax-conscious investor in India,  
**I want** ArthSaarthi to automatically apply statutory capital loss set-off rules (STCL vs STCG/LTCG, LTCL vs LTCG only), maintain a carry-forward loss ledger across assessment years (8-year limit), and suggest tax-loss harvesting opportunities from open positions,  
**so that** I can minimize my net taxable capital gains and optimize my tax liability under the Income-tax Act.

---

### 2. Functional Requirements

* [ ] **Intra-Head Set-Off Engine:** Implement `TaxSetOffService` applying Section 70/71/74 set-off rules to net realized gains (STCL against STCG/LTCG; LTCL against LTCG only).
* [ ] **Carry-Forward Loss Ledger Database & API:** Create `CapitalLossLedger` model, Alembic migration, schemas, and REST CRUD endpoints (`/api/v1/capital-gains/loss-ledger`).
* [ ] **Tax-Loss Harvesting Recommendations Engine:** Scan open tax lots with negative unrealized gains and compute potential tax savings by harvesting STCL/LTCL before FY end (`/api/v1/capital-gains/tax-loss-harvesting`).
* [ ] **Frontend Loss Ledger & Harvesting UI:** Create `CapitalLossLedgerModal`, `CapitalGainsNetSummaryCard`, and `TaxLossHarvestingCard` on `CapitalGainsPage.tsx` with Privacy Mode support.
* [ ] **Automated Test Coverage:** Add comprehensive backend pytest cases (`test_tax_setoff_service.py`) and frontend Jest unit tests.

---

### 3. Acceptance Criteria

* [ ] **Scenario 1:** Given a user with realized STCL of ₹20,000 and realized LTCG of ₹50,000, when viewing the Capital Gains Net Summary, then STCL is set off against LTCG, reducing net LTCG.
* [ ] **Scenario 2:** Given a user with realized LTCL of ₹30,000 and realized STCG of ₹40,000, when viewing the Net Summary, then LTCL is NOT set off against STCG, and LTCL is marked as unabsorbed to be carried forward.
* [ ] **Scenario 3:** Given an open stock position trading at an unrealized loss, when requesting Tax-Loss Harvesting suggestions, then the engine recommends selling that lot to offset realized STCG/LTCG with projected tax savings.

---

### 4. Dependencies

* Depends on Tax Lot Accounting (`FR4.4.3`), Realized Capital Gains Engine (`FR6.5`), and Unrealized Capital Gains Engine (`FR6.5 Phase 2 / FR6.5.7`).

---

### 5. Additional Context

* **Requirement ID:** `(FR6.5 Phase 3 / FR6.5.8)`
* **Specification File:** [`docs/features/FR6.5.8_capital_loss_setoff_and_harvesting.md`](file:///media/data/AppData/CodeServer/pms4/ArthSaarthi/docs/features/FR6.5.8_capital_loss_setoff_and_harvesting.md)
