# Functional Requirement Specification: Automated Bond Corporate Actions (Coupons & Maturity Redemptions)

**Feature ID:** FR-CorporateActions-Bond-Automation  
**GitHub Issue:** [#562](https://github.com/aashishbhanawat/ArthSaarthi/issues/562)  
**Parent Requirement:** FR4.6 (Corporate Actions) & FR17 (Background Task & Job Scheduling Engine)  
**Target Release:** v1.5.0  
**Status:** In Review / Specification  

---

## 1. Sub-component Breakdown & Micro-Phases

### Phase 1: Bond Coupon & Schedule Calculation Engine
- Pure Python date math module to calculate expected coupon payout dates based on `payment_frequency` (`ANNUALLY`, `SEMI_ANNUALLY`, `QUARTERLY`, `MONTHLY`, `ON_MATURITY`), `first_payment_date`, and `maturity_date`.
- Accurately compute per-unit and total holding coupon credit:
  $$\text{Coupon Payout} = \frac{\text{Face Value} \times \frac{\text{Coupon Rate}}{100}}{\text{Frequency Divisor}} \times \text{Holding Quantity}$$
  where Frequency Divisor = 1 (Annual), 2 (Semi-Annual), 4 (Quarterly), 12 (Monthly).
- Strictly idempotent: Before generating any coupon credit, verify no matching `COUPON` transaction exists for the `(portfolio_id, asset_id, payout_date)`.

### Phase 2: Bond Maturity Auto-Redemption Engine
- Scheduler job checks if the current date matches or exceeds `maturity_date` for bonds held in user portfolios.
- If the user holds `N > 0` units of the bond on or after `maturity_date`, automatically generate a redemption transaction:
  - `transaction_type = "SELL"`
  - `quantity = N`
  - `price_per_unit = face_value` (defaulting to 1000 if not specified)
  - `transaction_date = maturity_date`
  - `is_automated = True`
- Closes the active holding lot and releases principal back into portfolio cash balance.
- If `payment_frequency == "ON_MATURITY"`, also generate the final cumulative coupon payment.

### Phase 3: Database Schema & Migration
- Extend `transactions` table with an indexed `is_automated` boolean column (default `False`).
- Create `corporate_action_events` table to track auto-generated corporate actions, provide user notification state (`NEW`, `READ`, `DISMISSED`), and link directly to generated transactions.

### Phase 4: Background Task Worker in APScheduler
- Create `backend/app/tasks/corporate_actions_task.py` and register `process_bond_corporate_actions` job in `app/tasks/registry.py`.
- Scheduled to run daily at 00:15 UTC (or manually triggered via the Automated Tasks admin dashboard).
- Wrapped with try/except, logging, execution metrics, and rollback on error.

### Phase 5: REST API Endpoints
- Endpoints under `/api/v1/corporate-actions`:
  - `GET /events`: Fetch corporate action events for the authenticated user's portfolios (filterable by status: `NEW`, `READ`, `DISMISSED`).
  - `POST /events/{event_id}/dismiss`: Mark an event as dismissed.
  - `POST /events/dismiss-all`: Dismiss all unread events.
  - `POST /admin/process-bonds`: Admin trigger to execute bond corporate action processing immediately.

### Phase 6: Frontend Notification & Review UI
- Add a notification indicator in the main navigation bar displaying an alert badge when new automated corporate action events are pending review.
- Clicking the notification opens `CorporateActionNotificationModal`:
  - Summarizes newly credited coupon payouts and matured bond redemptions.
  - Shows Bond Name, Payout Date, Units Held, Amount Credited, and a direct link to the transaction.
  - "Dismiss All" and individual "Dismiss" actions.
- Display a subtle `[Automated]` badge in transaction history tables and cards.

---

## 2. Technical Specification (Backend & Frontend)

### 2.1 Backend Implementation Details
- **Engine (`backend/app/services/corporate_actions/bond_engine.py`):**
  - `is_coupon_due(bond: Bond, check_date: date) -> bool`: Checks if `check_date` is a valid scheduled coupon date.
  - `calculate_coupon_amount(bond: Bond, quantity: Decimal) -> Decimal`: Precision decimal arithmetic for coupon payments.
  - `process_portfolio_bonds(db: Session, check_date: date) -> List[CorporateActionEvent]`: Evaluates all active portfolios with bond holdings, generates `COUPON` and `SELL` (maturity) transactions, and records `CorporateActionEvent` rows.
- **Worker (`backend/app/tasks/corporate_actions_task.py`):**
  - Integrated with `AsyncIOScheduler` via `app.core.scheduler`.
  - Captures execution stats and errors in `scheduled_job_logs`.

### 2.2 Frontend Implementation Details
- **API Client (`frontend/src/services/corporateActionsApi.ts`):**
  - Methods to fetch events, dismiss events, and trigger manual processing.
- **Notification Component (`frontend/src/components/Notifications/CorporateActionNotificationModal.tsx`):**
  - Responsive modal dialog showing automated activity receipts.
  - Mobile card layout for small screens.
- **Navbar Integration (`frontend/src/components/Layout/Navbar.tsx`):**
  - Bell / Notification icon with badge count.

---

## 3. Comprehensive Test Plan & Edge Cases

### 3.1 Edge Cases & Failure Scenarios
1. **Idempotency on Multiple Runs:** If the job runs multiple times on the same day (or admin triggers it repeatedly), exactly ONE coupon transaction is generated per holding per scheduled date.
2. **Weekend & Month-End Alignment:** Handles 30-day months, 31-day months, leap years (Feb 29), and non-leap years (Feb 28). If a semi-annual bond is issued on Aug 31, the second coupon lands on Feb 28 (or Feb 29).
3. **Zero Holdings on Payout Date:** If a user bought and subsequently sold 100% of their bond before the coupon date, no coupon is created.
4. **Partial Sells Before Maturity:** If a user bought 100 units, sold 40 units, only the remaining 60 units are redeemed at maturity.
5. **Multiple Portfolios Holding Same Bond:** Both portfolios receive independent coupon credits matching their respective quantities.
6. **Matured Bonds Already Redeemed:** Once a bond is redeemed, subsequent runs must not create redundant sell transactions.
7. **Missing Bond Face Value:** Fallback gracefully to default face value (1,000 INR) if `face_value` is `None`.

### 3.2 Manual Testing Checklist
- [ ] Add a Bond holding with annual coupon payout matching today's date.
- [ ] Navigate to Admin > Automated Tasks, click **Run Now** for the corporate actions task.
- [ ] Verify success notification message.
- [ ] Verify new `COUPON` transaction in Transaction History with `[Automated]` badge.
- [ ] Verify notification bell displays badge count "1".
- [ ] Open notification modal, verify coupon details, and click "Dismiss".
- [ ] Verify notification count resets to 0.

---

## 4. Automated Testing Strategy

### 4.1 Backend Pytest
- `backend/app/tests/services/test_bond_engine.py`: Test date math across Annual, Semi-Annual, Quarterly, Monthly frequencies, leap years, and month-end dates.
- `backend/app/tests/tasks/test_corporate_actions_task.py`: Test end-to-end task execution, idempotency, transaction creation, cash updates, and event logging.
- `backend/app/tests/api/v1/test_corporate_actions.py`: Test authentication, event listing, dismiss endpoints, and admin manual trigger.
- **SQLite + Desktop Compatibility Test:** Verify migration and queries work seamlessly on SQLite.

### 4.2 Frontend Unit Tests
- `frontend/src/components/Notifications/CorporateActionNotificationModal.test.tsx`: Test rendering event cards, dismiss interactions, and empty states.
- `frontend/src/components/Layout/Navbar.test.tsx`: Test unread badge rendering when pending events exist.

### 4.3 E2E Playwright Tests
- `e2e/tests/automated-bond-corporate-actions.spec.ts`: End-to-end verification of bond creation, coupon trigger, notification alert, and transaction list verification.

---

## 5. UX & UI Specifications
- **Notification Bell in Navigation:** Subtle bell icon in header with an emerald/indigo badge displaying unread corporate action receipts.
- **Receipts Modal:** Clean dialog displaying:
  - Header: *"Automated Activity"*
  - Cards: Bond name, Action (`Interest/Coupon Payment` or `Bond Maturity Redemption`), Date, Units, and Total Amount Credited.
  - Actions: *"Dismiss All"* and individual *"Dismiss"*.
- **Transaction Badging:** Transactions generated by the background scheduler display a subtle pill badge: `[Automated]`.

---

## 6. Database Schema & Data Security

### 6.1 Database Schema Changes
1. **Add column to `transactions`:**
   ```sql
   ALTER TABLE transactions ADD COLUMN is_automated BOOLEAN NOT NULL DEFAULT FALSE;
   CREATE INDEX ix_transactions_is_automated ON transactions(is_automated);
   ```

2. **Create table `corporate_action_events`:**
   ```sql
   CREATE TABLE corporate_action_events (
       id UUID PRIMARY KEY,
       user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
       portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
       transaction_id UUID REFERENCES transactions(id) ON DELETE SET NULL,
       asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
       event_type VARCHAR(50) NOT NULL, -- 'BOND_COUPON', 'BOND_MATURITY'
       event_date DATE NOT NULL,
       units NUMERIC(18, 8) NOT NULL,
       amount NUMERIC(18, 8) NOT NULL,
       status VARCHAR(20) NOT NULL DEFAULT 'NEW', -- 'NEW', 'READ', 'DISMISSED'
       details JSON,
       created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
   );
   CREATE INDEX ix_corporate_action_events_user_status ON corporate_action_events(user_id, status);
   ```

### 6.2 Data Security & Encryption
- Standard financial amounts, units, and dates; no personal secret keys or credentials are stored.
- SQLite encrypted database compatible (no unencrypted raw PII).

---

## 7. Required Documentation Updates
- **README.md:** Add entry for automated bond coupon payments & maturity tracking.
- **docs/code_flow_guide.md:** Add architectural lifecycle and execution diagram for bond corporate actions.
- **docs/architecture.md:** Document `bond_engine` and `corporate_action_events` integration.
- **docs/debugging_guide.md:** Add troubleshooting guide for inspecting automated corporate actions and reverting transactions.
- **docs/workflow_history.md:** Document implementation steps and verification.
- **docs/project_handoff_summary.md:** Update feature status.
- **docs/requirements.md:** Mark automated corporate actions for bonds as implemented.

---

## 8. External Data Sources Required
- **None:** Purely deterministic calculation using internal stored data in `assets` and `bonds` tables (`coupon_rate`, `payment_frequency`, `maturity_date`, `face_value`, `first_payment_date`) and active portfolio holdings. Zero external third-party API dependencies.

---

## 9. File & API Endpoint Inventory

### Backend Files to Create/Modify
- **Create:** `backend/alembic/versions/l12e4f5g6h7i_add_bond_corporate_actions.py`
- **Create:** `backend/app/models/corporate_action_event.py`
- **Create:** `backend/app/schemas/corporate_action.py`
- **Create:** `backend/app/crud/crud_corporate_action_event.py`
- **Create:** `backend/app/services/corporate_actions/__init__.py`
- **Create:** `backend/app/services/corporate_actions/bond_engine.py`
- **Create:** `backend/app/tasks/corporate_actions_task.py`
- **Create:** `backend/app/api/v1/endpoints/corporate_actions.py`
- **Modify:** `backend/app/models/transaction.py` (add `is_automated`)
- **Modify:** `backend/app/models/__init__.py` (export `CorporateActionEvent`)
- **Modify:** `backend/app/tasks/registry.py` (register corporate actions task)
- **Modify:** `backend/app/api/v1/api.py` (mount corporate actions router)

### Frontend Files to Create/Modify
- **Create:** `frontend/src/types/corporateActions.ts`
- **Create:** `frontend/src/services/corporateActionsApi.ts`
- **Create:** `frontend/src/components/Notifications/CorporateActionNotificationModal.tsx`
- **Modify:** `frontend/src/components/Layout/Navbar.tsx` (add notification bell with badge)
- **Modify:** `frontend/src/components/Transactions/TransactionCard.tsx` (display `[Automated]` badge)
- **Modify:** `frontend/src/components/Transactions/TransactionTable.tsx` (display `[Automated]` badge)

---

## 10. Mobile-Friendly UI & Responsive Design
- Notification bell button with touch-friendly 44px hit target.
- Modal dialog collapses into a full-width bottom sheet / stacked card list on viewports `< 768px`.
- One-tap "Dismiss All" button easily accessible on mobile.

---

## 11. Android Compatibility & Python Runtime Constraints
- Pure Python implementation using standard libraries: `datetime`, `decimal.Decimal`, `calendar`, `uuid`, and SQLAlchemy.
- Zero native C-extensions or external binary dependencies; 100% compatible with Chaquopy (Android) and local SQLite desktop builds.
