# Functional Requirement Specification: Automated Corporate Actions

**Feature ID:** FR-CorporateActions-Automation  
**GitHub Issue:** [#562](https.github.com/aashishbhanawat/ArthSaarthi/issues/562)  
**Title:** Automated Corporate Action Processing (Bond Coupons & Maturity Auto-Generation)  
**Target Release:** v1.5.0  

---

## 1. Sub-component Breakdown & Micro-Phases

### Phase 5.1: Bond Coupon Auto-Generation Engine
* Scheduler task (`process_bond_coupons_job`) checking all user Bond holdings daily at midnight.
* Calculate expected payout date based on bond coupon rate, payment frequency (Annual, Semi-Annual, Quarterly, Monthly), and issue date.
* Automatically generate income transaction (`DIVIDEND` / `COUPON`) credited to user's portfolio cash balance on payment date.

### Phase 5.2: Bond Maturity Auto-Redemption Engine
* Scheduler task (`process_bond_maturities_job`) checking bond maturity dates.
* On maturity date, automatically generate redemption transaction (`SELL`) at face value, closing the active holding lot and releasing principal.

### Phase 5.3: User Notification & Approval Workflow
* Notification banner / toast informing user of auto-generated corporate action transactions.
* Audit trail allowing user to view, edit, or revert automatically generated corporate action entries.

---

## 2. Technical Specification (Backend & Frontend)

### 2.1 Backend Implementation Details
* **Task Worker (`backend/app/tasks/corporate_actions_task.py`):**
  * `process_daily_bond_corporate_actions(db)` function.
  * Queries active `Asset` entries of type `BOND` with non-null coupon frequency and maturity date.
  * Idempotency protection: Checks if transaction already exists for specific asset, user, date, and type before inserting.

### 2.2 Frontend Implementation Details
* **Notifications Modal (`src/components/notifications/CorporateActionNotificationModal.tsx`):**
  * Displays list of newly generated coupon payouts and maturity redemptions with option to confirm or adjust values.

---

## 3. Comprehensive Test Plan & Edge Cases

### 3.1 Edge Cases & Failure Scenarios
* **Idempotency / Duplicate Run:** Running job multiple times on same day MUST NOT create duplicate coupon transactions.
* **Leap Year / Weekend Payment Dates:** Payout falling on weekend (e.g. Sunday) credited on next business day or exact coupon date based on standard day-count convention (30/360 or Actual/Actual).
* **Zero Holdings on Payout Date:** If user sold bond prior to record date, coupon transaction must not be created.

### 3.2 Manual Testing Checklist
* [ ] Add a Bond holding with semi-annual coupon payout set for today's date.
* [ ] Trigger background job manually via Admin Scheduler dashboard.
* [ ] Verify coupon income transaction created in portfolio transaction history.
* [ ] Verify portfolio cash and total returns updated accordingly.

---

## 4. Automated Testing Strategy

### 4.1 Backend Pytest (`backend/app/tests/tasks/test_corporate_actions_task.py`)
* Test coupon calculation for Annual, Semi-Annual, Quarterly, and Monthly bonds.
* Test bond maturity redemption logic and holding status update.
* Test idempotency key checks.

### 4.2 Frontend Vitest (`src/components/notifications/__tests__/CorporateActionModal.test.tsx`)
* Test displaying auto-generated transaction alerts and user edit options.

### 4.3 E2E Playwright (`tests/automated-corporate-actions.spec.ts`)
* End-to-end simulation of bond maturity trigger and dashboard verification.

---

## 5. UX & UI Specifications
* Notification badge in navigation header highlighting pending auto-generated corporate action receipts.
* Visual badge tag in Transaction History marking transactions as `[Auto-Generated]`.

---

## 6. Database Schema & Data Security

### 6.1 Database Schema
Extend `transactions` table with `is_automated` boolean flag and `automation_rule_id` column:

```sql
ALTER TABLE transactions ADD COLUMN is_automated BOOLEAN DEFAULT FALSE;
ALTER TABLE transactions ADD COLUMN automation_metadata JSONB NULL;
```

### 6.2 Encryption Requirements
* Standard financial amounts (INR/USD); no encryption required for transaction rows.

---

## 7. Required Documentation Updates

* **README.md:** Add documentation on automated bond coupon and maturity tracking.
* **docs/code_flow_guide.md:** Document corporate action auto-generation lifecycle.
* **docs/workflow_history.md:** Add entry upon feature completion.
* **docs/debugging_guide.md:** Document how to audit or revert automated corporate action transactions.
* **docs/project_handoff_summary.md:** Update corporate actions feature status.
* **docs/requirements.md:** Mark automated corporate actions as `✅ Implemented`.

---

## 8. External Data Sources & API Specifications
* Internal calculation using stored Asset master record attributes (ISIN, coupon_rate, coupon_frequency, maturity_date).

---

## 9. File & API Endpoint Inventory

### Files to Create / Modify
* **Create:** `backend/app/tasks/corporate_actions_task.py`
* **Create:** `backend/app/services/corporate_action_automation.py`
* **Create:** `frontend/src/components/notifications/CorporateActionNotificationModal.tsx`
* **Modify:** `backend/app/models/transaction.py`
* **Modify:** `backend/app/crud/crud_transaction.py`

### API Routes
* `GET /api/v1/corporate-actions/pending` - Fetch auto-generated transactions requiring user review
* `POST /api/v1/corporate-actions/confirm` - Confirm auto-generated transaction

---

## 10. Mobile-Friendly UI & Responsive Design
* Mobile alert modal listing auto-generated corporate action receipts with swipe-to-dismiss or confirm controls.

---

## 11. Android Compatibility & Python Library Constraints
* 100% Python standard library date math (`datetime`, `dateutil.relativedelta`); fully compatible with Android Python runtimes.
