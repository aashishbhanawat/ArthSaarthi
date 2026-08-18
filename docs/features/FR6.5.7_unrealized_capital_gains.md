# Feature Specification: Unrealized Capital Gains & Exemption Pooling (FR6.5 Phase 2)

**Feature ID:** FR6.5 Phase 2 (FR6.5.7)  
**Status:** 📝 Planned  
**Title:** Unrealized Capital Gains Calculation & Section 112A Exemption Pooling  
**GitHub Issue:** [#516](https://github.com/aashishbhanawat/ArthSaarthi/issues/516)  
**User Story:** As an investor, I want to calculate and view unrealized capital gains and Section 112A exemption usage across active holdings, so that I can make tax-optimized sell decisions and plan tax-loss harvesting.

---

## 1. Sub-Task Breakdown & Implementation Modules

1. **Module 1.1 (Backend Engine):** Unrealized gain math engine (`UnrealizedTaxService`) computing lot-level FIFO unrealized STCG/LTCG and Section 112A exemption pooling.
2. **Module 1.2 (Backend API):** REST endpoint `GET /api/v1/tax/unrealized-gains` with user tenant isolation and portfolio filtering.
3. **Module 1.3 (Frontend UI):** Unrealized Capital Gains card on Capital Gains page, Section 112A headroom progress meter, and tax lot drilldown modal.

---

## 2. Backend & Frontend Responsibilities

* **Backend (`backend/app/services/unrealized_tax_service.py`):**
  - Fetch active holdings and tax lots.
  - Query live market prices (`FinancialDataService`).
  - Calculate lot holding days, classify as STCG/LTCG.
  - Pool Section 112A LTCG exemptions (₹1,25,000 threshold).
* **Frontend (`frontend/src/components/UnrealizedGainsModal.tsx` & `CapitalGainsPage.tsx`):**
  - Render summary cards (Total Unrealized STCG, LTCG, Section 112A Headroom, Tax Estimate).
  - Modal displaying tax-lot breakdowns per asset.
  - Privacy Mode currency masking (`usePrivacySensitiveCurrency`).

---

## 3. Test Plan & Corner Cases

### 3.1. Corner Cases
* **Loss-Making Lots:** Holdings in loss (negative unrealized gains) properly offset total gains where applicable, identifying Tax-Loss Harvesting opportunities.
* **Partial Section 112A Headroom:** If realized LTCG consumed ₹1,00,000, remaining exemption headroom for unrealized gains displays ₹25,000.
* **Unmapped Market Assets:** Assets without live prices fallback gracefully to last available transaction cost or manual price input without crashing.

### 3.2. Manual Testing Matrix
* [ ] Verify unrealized gains update when market prices refresh.
* [ ] Test toggling Privacy Mode and verify amounts are masked (`***`).
* [ ] Verify responsive card layout on mobile viewports.

---

## 4. Test Automation Plan

* **Backend Tests (`app/tests/api/v1/test_unrealized_tax.py`):** Unit and integration tests verifying lot calculations, holding period boundaries, and exemption pooling.
* **Frontend Tests (`src/components/UnrealizedGainsModal.test.tsx`):** Component tests for card rendering and lot table.
* **E2E Tests (`tests/tax-readiness-workflow.spec.ts`):** E2E test verifying capital gains page navigation and unrealized tab.

---

## 5. UX & UI Specifications

* **Design:** Emerald badges for LTCG exemption headroom, Amber badges for STCG tax projections.
* **Components:** Summary metrics grid, exemption progress bar, lot breakdown table.

---

## 6. Database Schema & Security Encryption (`EncryptedString`)

* Computes data dynamically from existing `transactions` and `holdings` tables.
* Relies on `Transaction` and `Holding` encrypted columns where applicable under local SQLite DB mode.

---

## 7. Documentation Updates Roadmap

* **`docs/code_flow_guide.md`**: Document `UnrealizedTaxService` data flow.
* **`docs/workflow_history.md`**: Log implementation progress.
* **`docs/project_handoff_summary.md`**: Update test counts.
* **`docs/requirements.md`**: Mark `FR6.5.3` as `✅ Done`.

---

## 8. Data Sources Required

* **Market Prices:** `FinancialDataService` (Upstox V3 primary, yfinance fallback).
* **Statutory Rates:** Section 112A LTCG rate (12.5%), Section 111A STCG rate (20%), Section 112A threshold (₹1,25,000).

---

## 9. Files & APIs to Create / Update

* `backend/app/services/unrealized_tax_service.py` (New)
* `backend/app/api/v1/endpoints/tax_summary.py` (Update)
* `frontend/src/components/UnrealizedGainsModal.tsx` (New)
* `backend/app/tests/api/v1/test_unrealized_tax.py` (New)

---

## 10. Mobile-Friendly UI

* `pt-safe` and `pb-safe` spacing for mobile headers/notches.
* Touch-scroll wrappers for tax lot data tables.

---

## 11. Android Compatible Python Libraries

* Built strictly with standard Python `decimal.Decimal` and `datetime` modules.
* Zero external native C-extensions (100% Chaquopy Android compatible).
