# FR: Automated Stock Corporate Actions & Dividend Fetching (Issue #607)

**Version:** 1.0  
**Date:** 2026-11-17  
**Status:** 📝 Proposed  
**Related PRs / Issues:** #607, #562, #609  
**Target Release:** v1.5.0  

---

## 1. Executive Summary & Objective

In Release v1.5.0, ArthSaarthi introduced architectural background job scheduling and automated bond corporate actions (coupons and maturity redemptions via Issue #562). 

While bond corporate actions are strictly deterministic and calculated from internal database metadata, **equity holdings (stocks and ETFs)** undergo external corporate actions declared by issuers on financial exchanges:
1. **Cash Dividends:** Periodic cash distributions per share declared on a record/ex-date.
2. **Stock Splits:** Sub-division of existing shares into multiple shares at an exchange ratio (e.g., 2-for-1, 10-for-1).
3. **Bonus Issues:** Capitalization of reserves into fully paid-up bonus shares issued to existing shareholders at a ratio (e.g., 1-for-1).

Currently, users must manually discover and record stock corporate actions through manual transaction entry ([`FR4.6_corporate_actions.md`](file:///media/data/AppData/CodeServer/pms4/ArthSaarthi/docs/features/FR4.6_corporate_actions.md)). 

**Objective:** Build an automated equity corporate actions engine integrated with the background scheduler to periodically fetch exchange corporate actions, discover applicable actions for user holdings, apply them with exact cost-basis accounting, and alert users via activity notifications.

---

## 2. Scope & Boundaries

### 2.1 In Scope
- **Asset Classes:** Stocks (`AssetType.STOCK`) and Exchange Traded Funds (`AssetType.ETF`) held in any active portfolio (both Indian equities on NSE/BSE and Foreign/US equities).
- **Corporate Action Types:**
  - **Dividends:** Fetch dividend per share and ex-date. Calculate total dividend credit based on holding quantity as of ex-date.
  - **Stock Splits:** Fetch split ratio and ex-date. Automatically adjust prior purchase lots and cost-per-share using established `handle_stock_split` logic.
  - **Bonus Issues:** Fetch bonus ratio and ex-date. Generate 0-cost acquisition transactions for new shares using established `handle_bonus_issue` logic.
- **Data Providers:**
  - Pluggable provider method `get_corporate_actions(ticker, exchange)` in `FinancialDataProvider`.
  - Primary implementation in `YFinanceProvider` utilizing `yfinance.Ticker.actions`, `.dividends`, and `.splits`.
- **Background Scheduler Integration:**
  - Register `stock_corporate_actions` job in `app.tasks.registry` (daily cron in server mode, periodic interval in desktop/android mode).
- **User Activity Notification:**
  - Reuse the existing `corporate_action_events` table and the `CorporateActionNotificationModal.tsx` notification bell.
  - Show clear activity receipts for credited dividends, splits, and bonus issues.
- **Idempotency & Catch-Up:**
  - Deduplicate across existing transactions and events to guarantee zero duplicate credits.
  - Support automatic catch-up across machine downtime or app inactivity.

### 2.2 Out of Scope
- Fixed Income / Bond coupons and redemptions (already completed under Issue #562).
- Automatic bank account funds transfer (virtual cash balance tracking only).
- Mergers and demergers requiring manual share swaps or capital reorganizations (remains manual entry).

---

## 3. Architecture & Technical Design

### 3.1 Data Flow Diagram

```
+-------------------------------------------------------------+
|                     APScheduler                             |
|  (Daily Server Cron: 00:30 | Desktop/Android: Interval)     |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|          Stock Corporate Actions Task (Async Worker)        |
|          `app/tasks/stock_corporate_actions_task.py`        |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                   Stock Engine & Fetcher                    |
|      `app/services/corporate_actions/stock_engine.py`       |
+------------------------------+------------------------------+
                               |
      +------------------------+------------------------+
      | Queries active stock                            | Calls Provider for
      | holdings per portfolio                          | Corporate Actions feed
      v                                                 v
+-----------------------------+               +-----------------------------+
|    Portfolios & Holdings    |               |       YFinanceProvider      |
|     (Active Stock Units)    |               |   `.actions` / `.splits`    |
+-----------------------------+               +-----------------------------+
                               \               /
                                \             /
                                 v           v
+-------------------------------------------------------------+
|                Corporate Action Evaluator                   |
| 1. Checks (portfolio_id, asset_id, type, date) idempotency   |
| 2. Evaluates holding quantity on ex-date                    |
| 3. Computes dividend credit or split/bonus ratio            |
| 4. Calls `crud_corporate_action` for splits and bonuses     |
| 5. Creates `Transaction` with `is_automated=True`           |
| 6. Creates `CorporateActionEvent` (`status="NEW"`)           |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                  User Notification System                   |
|     `GET /api/v1/corporate-actions/events`                  |
|     `CorporateActionNotificationModal.tsx` (Navbar Bell)    |
+-------------------------------------------------------------+
```

---

## 4. Detailed Component Specifications

### 4.1 Data Provider Extension (`backend/app/services/providers/`)
Add `get_corporate_actions(self, ticker_symbol: str, exchange: Optional[str] = None) -> List[Dict[str, Any]]` to `FinancialDataProvider` interface:
- Returns list of normalized corporate action records:
  - `action_type`: `"DIVIDEND"`, `"SPLIT"`, or `"BONUS"`
  - `date`: `date` (ex-date / record date)
  - `value`: `Decimal` (cash amount per share for dividend, or ratio numerator)
  - `ratio_denominator`: `Optional[Decimal]` (e.g. 1 for 2:1 split)
  - `raw_details`: `Dict[str, Any]`
- Implement in `YFinanceProvider` with caching to avoid rate-limiting.

### 4.2 Stock Corporate Action Engine (`backend/app/services/corporate_actions/stock_engine.py`)
- `get_active_stock_assets(db: Session) -> List[Asset]`: Returns unique stock/ETF assets currently held with positive quantities.
- `evaluate_dividend(db, portfolio, asset, action_date, dividend_per_share)`:
  - Verifies holding quantity on `action_date`.
  - Checks if `DIVIDEND` transaction on `action_date` already exists.
  - If new: creates automated `DIVIDEND` transaction and `CorporateActionEvent`.
- `evaluate_stock_split(db, portfolio, asset, action_date, split_ratio)`:
  - Verifies holding exists prior to `action_date`.
  - Checks if `SPLIT` event already processed for `(portfolio, asset, action_date)`.
  - If new: invokes `crud.crud_corporate_action.handle_stock_split` and creates `CorporateActionEvent`.
- `evaluate_bonus_issue(db, portfolio, asset, action_date, bonus_ratio)`:
  - Verifies holding exists prior to `action_date`.
  - Checks if `BONUS` event already processed for `(portfolio, asset, action_date)`.
  - If new: invokes `crud.crud_corporate_action.handle_bonus_issue` and creates `CorporateActionEvent`.

### 4.3 Background Scheduler Integration
- Job ID: `stock_corporate_actions`
- Trigger: `CronTrigger(hour=0, minute=30)` in server mode, `IntervalTrigger(hours=6)` in desktop/android mode.
- Non-blocking execution using `loop.run_in_executor`.

### 4.4 Admin Trigger API
- `POST /api/v1/corporate-actions/admin/process-stocks`: Allows admins to immediately trigger equity corporate actions discovery from the admin dashboard or tests.

### 4.5 User Interface Updates
- Reuses existing notification bell in `NavBar.tsx` and `MobileHeader.tsx`.
- Modal displays:
  - **Stock Dividend:** `"Dividend Payout"`, ticker name, dividend per share, total cash credited, and ex-date.
  - **Stock Split:** `"Stock Split"`, ticker name, split ratio (e.g. 2 for 1), updated total shares, and effective date.
  - **Bonus Issue:** `"Bonus Shares"`, ticker name, bonus ratio (e.g. 1 for 2), new shares received, and effective date.
- Transaction history displays `[Automated]` badge.

---

## 5. Test Plan & Edge Cases

1. **Zero Holdings on Ex-Date:** User held 0 shares on ex-date $\rightarrow$ No dividend or split processed.
2. **Shares Bought on/after Ex-Date:** Shares purchased on or after ex-date are not eligible for the dividend.
3. **Idempotency on Repeated Execution:** Running the job 5 times produces exactly 1 transaction per event.
4. **Historical Backfill / Downtime Catch-Up:** Missed events during system downtime are discovered and posted with the original ex-date.
5. **Partial Sells Prior to Split:** Split ratio applies only to un-sold historical lots.
6. **Cross-Platform Compatibility:** Runs cleanly on PostgreSQL, SQLite desktop mode, and Android.
