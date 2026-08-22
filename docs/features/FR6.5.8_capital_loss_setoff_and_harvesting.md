# Feature Specification: Intra-Head Capital Loss Set-Off, Loss Ledger & Tax-Loss Harvesting (FR6.5 Phase 3)

**Feature ID:** FR6.5 Phase 3 (FR6.5.8)  
**Feature Name:** Capital Loss Set-Off Engine, Carry-Forward Loss Ledger & Tax-Loss Harvesting  
**Target Release:** Release v1.4.0  
**Status:** In Plan  

---

## 1. Executive Summary & Objective

In accordance with the Income-tax Act, 1961 (and Income-tax Act, 2026 amendments), capital losses incurred in a financial year are subject to strict statutory intra-head set-off rules and carry-forward restrictions:
1. **Short-Term Capital Loss (STCL):** Can be set off against both Short-Term Capital Gains (STCG) and Long-Term Capital Gains (LTCG).
2. **Long-Term Capital Loss (LTCL):** Can **only** be set off against Long-Term Capital Gains (LTCG). LTCL cannot be set off against STCG.
3. **Carry-Forward Duration:** Unabsorbed capital losses can be carried forward for up to **8 Assessment Years (AY)** immediately succeeding the loss year, provided the return of income was filed on or before the due date specified under Section 139(1).

This feature introduces a statutory **Intra-Head Capital Loss Set-Off Engine**, a persistent **Carry-Forward Loss Ledger** (with an 8-year countdown tracking meter), and an interactive **Tax-Loss Harvesting Recommendations Engine** to calculate net taxable gains and suggest tax-optimized sell actions before the FY close.

---

## 2. Statutory Set-Off Rules & Priority Ordering

### A. Intra-Year Set-Off Matrix (Current Financial Year)
When calculating realized tax liabilities for the financial year:
- **STCL Allocation:** Set off against highest-taxed STCG first (Slab Rate 30% / 20% Sec 111A), then against taxable LTCG 12.5% in excess of Section 112A headroom.
- **LTCL Allocation:** Set off against taxable LTCG 12.5% in excess of Section 112A headroom. Cannot touch STCG.

### B. Brought-Forward Losses (Prior Assessment Years)
- Brought-forward STCL is set off against remaining current year STCG / LTCG.
- Brought-forward LTCL is set off against remaining current year LTCG only.
- Expired losses (>8 Assessment Years old) or losses marked as filed late (`is_itr_filed_on_time = False`) are excluded from set-off calculations.

---

## 3. Database Schema (`CapitalLossLedger`)

Create SQLAlchemy database model `CapitalLossLedger` in `backend/app/models/capital_loss_ledger.py`:

```python
class CapitalLossLedger(Base):
    __tablename__ = "capital_loss_ledgers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    financial_year = Column(String(7), nullable=False) # e.g. "2023-24"
    assessment_year = Column(String(7), nullable=False) # e.g. "2024-25"
    stcl_amount = Column(Numeric(14, 2), nullable=False, default=0.0)
    ltcl_amount = Column(Numeric(14, 2), nullable=False, default=0.0)
    is_itr_filed_on_time = Column(Boolean, nullable=False, default=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

---

## 4. Backend Service Engine (`TaxSetOffService`)

Create `backend/app/services/tax_setoff_service.py`:
1. `calculate_net_capital_gains(user_id, fy_year, portfolio_id, slab_rate)`:
   - Computes gross realized STCG, STCL, LTCG, LTCL for the FY via `CapitalGainsService`.
   - Fetches active brought-forward loss ledger entries for `user_id`.
   - Executes statutory intra-head set-off logic.
   - Computes Net Taxable STCG, Net Taxable LTCG, Net Taxable STCL unabsorbed, Net Taxable LTCL unabsorbed, and Total Net Tax.
2. `get_loss_harvesting_opportunities(user_id, fy_year, portfolio_id, slab_rate)`:
   - Evaluates open tax lots with negative unrealized gains from `UnrealizedTaxService`.
   - Computes potential tax savings by harvesting STCL vs 30%/20% STCG and LTCL vs 12.5% LTCG.
   - Returns ranked harvesting recommendations with step-by-step sell instructions.

---

## 5. API Endpoint Specifications

Register REST endpoints in `backend/app/api/v1/endpoints/capital_gains.py`:
- `GET /api/v1/capital-gains/set-off?fy={FY}` -> Returns net capital gains after intra-head and brought-forward set-off.
- `GET /api/v1/capital-gains/loss-ledger` -> List user's brought-forward loss ledger records.
- `POST /api/v1/capital-gains/loss-ledger` -> Create/Update brought-forward loss ledger record.
- `DELETE /api/v1/capital-gains/loss-ledger/{id}` -> Delete loss ledger record.
- `GET /api/v1/capital-gains/tax-loss-harvesting` -> Returns open tax lot harvesting suggestions and estimated tax savings.

---

## 6. Frontend UI Components

1. **`CapitalLossLedgerModal.tsx`:** Modal allowing users to view, add, edit, and manage brought-forward loss records by Assessment Year with an 8-year expiration indicator.
2. **`CapitalGainsNetSummaryCard.tsx`:** Card on `CapitalGainsPage.tsx` displaying Gross vs Set-Off vs Net Taxable Gains and Estimated Net Tax.
3. **`TaxLossHarvestingCard.tsx` & `TaxLossHarvestingModal.tsx`:** Card highlighting harvestable tax losses in open positions before FY end with projected tax savings.

---

## 7. Quality & Verification Plan
- Unit tests for statutory set-off ordering (`test_tax_setoff_service.py`).
- Frontend unit tests for loss ledger modal and tax loss harvesting cards.
- Full verification against Docker backend pytest test suite and frontend Jest test suite.
