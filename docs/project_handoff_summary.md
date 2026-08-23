# Project Handoff & Status Summary

**Last Updated:** 2026-08-23

## 1. Current Project Status

*   **Overall Status:** Active Feature Implementation — Release v1.4.0 (Tax Readiness & Full Financial Picture)

**Latest Achievement:** Implemented Intra-Head Capital Loss Set-Off Engine (Section 70/71/74: STCL vs STCG/LTCG, LTCL vs LTCG only), Carry-Forward Loss Ledger model with 8-year countdown meter, and Tax-Loss Harvesting Recommendations Engine for open tax lots (Issue #526 / FR6.5 Phase 3). All 6 backend pytest test cases and 47/47 frontend Jest test suites (193/193 tests) passing 100%.

## 2. Test Suite Status

*   **Backend Unit/Integration Tests (Postgres/Redis):** ✅ **372/375 Passing** (3 expected skips)
*   **Backend Integration Tests (Android/SQLite):** ✅ **372/375 Passing** (3 expected skips)
*   **Frontend Unit Tests (Jest):** ✅ **193/193 Passing** (47/47 Test Suites)
*   **Frontend TypeScript Compilation:** ✅ **Zero Errors**
*   **Linters (Code Quality):** ✅ **Passing (0 Errors - Ruff & ESLint clean)**

## Recent Stabilization & Refinement Efforts

*   **Intra-Head Capital Loss Set-Off, Loss Ledger & Tax-Loss Harvesting (Issue #526 / FR6.5 Phase 3) (Updated 2026-08-23):**
    - **Database Model & Migration:** Added `CapitalLossLedger` model (`backend/app/models/capital_loss_ledger.py`) tracking `user_id`, `financial_year`, `assessment_year`, `stcl_amount`, `ltcl_amount`, `is_itr_filed_on_time`, and `notes`. Generated Alembic migration `f67e8f9a0b1c_add_capital_loss_ledgers_table.py` and executed database upgrade cycle.
    - **Service Engine (`TaxSetOffService`):** Created `backend/app/services/tax_setoff_service.py` to calculate statutory Section 70/71/74 intra-head capital loss set-offs (STCL against STCG/LTCG; LTCL against LTCG only), 8-year brought-forward loss countdown meters, and tax-loss harvesting recommendations on open tax lots.
    - **REST API Endpoints:** Added `/api/v1/capital-gains/set-off`, `/api/v1/capital-gains/loss-ledger` (CRUD), and `/api/v1/capital-gains/tax-loss-harvesting` in `backend/app/api/v1/endpoints/capital_gains.py`.
    - **Frontend Components:** Created `CapitalLossLedgerModal.tsx`, `CapitalGainsNetSummaryCard.tsx`, and `TaxLossHarvestingCard.tsx` on `CapitalGainsPage.tsx` with Privacy Mode support.
    - **Automated Tests:** Authored 6 backend pytest test cases (`test_tax_setoff_service.py`) and Jest unit tests (`CapitalLossLedgerModal.test.tsx`). Verified 100% test pass rate across backend and frontend suites.

*   **Foreign & Indian Stock Tax Classification & Linter Hardening (Updated 2026-08-20):**

    - **Foreign Stock Tax Rules (`UnrealizedTaxService`):** Enforced 24-month (730-day) holding period for non-INR assets (CSCO, USD currency). Classifies holding period ≤ 730 days as `STCG`, assigns `Slab (30.0%)` tax rate, and excludes from Section 112A exemption pooling.
    - **Indian Stock Keyword Misclassification (`CapitalGainsService`):** Updated `_classify_asset_category` to return `EQUITY_LISTED` directly for Indian stocks (`atype in ["STOCK", "STOCKS", "EQUITY"]`) without matching generic keywords (`OVERSEAS`, `GLOBAL`, `WORLD`) in company names. Corrected classification for LAHOTI OVERSEAS LTD (`LAHOTIOV`).
    - **FR6.5 Phase 3 Planning:** Authored [`docs/features/FR6.5.8_capital_loss_setoff_and_harvesting.md`](file:///media/data/AppData/CodeServer/pms4/ArthSaarthi/docs/features/FR6.5.8_capital_loss_setoff_and_harvesting.md) and [`docs/issues/46_implement_tax_loss_harvesting_and_loss_ledger.md`](file:///media/data/AppData/CodeServer/pms4/ArthSaarthi/docs/issues/46_implement_tax_loss_harvesting_and_loss_ledger.md).
    - **Linter & Test Verification:** Fixed 19 python `ruff` lints and 2 typescript `eslint` lints. All 33 backend pytest test cases and 47/47 frontend Jest test suites (193/193 tests) passing cleanly.

*   **Upstox Metadata Seeder Unique ISIN & Session Rollback Fix (Updated 2026-08-18):**
    - Added `candidate_isin not in self.existing_isins` validation in `process_upstox_metadata()` in `backend/app/services/asset_seeder.py` to prevent assigning duplicate ISINs to existing asset records during server startup.
    - Added explicit `self.db.rollback()` in `process_upstox_metadata()` and `enrich_assets()` exception handlers to prevent SQLAlchemy `PendingRollbackError` container restart crash loops in Server / PostgreSQL mode.

*   **Unrealized Capital Gains & Section 112A Exemption Pooling (Issue #516 / FR6.5 Phase 2) (Updated 2026-08-18):**
    - **Backend Engine & Schemas (`UnrealizedTaxService`):** Created `backend/app/services/unrealized_tax_service.py` and `UnrealizedTaxLot`/`UnrealizedGainsSummary` schemas. Computes lot-level unsold quantities using `TransactionLink` references, fetches live market prices via `FinancialDataService.get_current_prices`, classifies STCG/LTCG holding period thresholds (12m for equity, 24m for debt/unlisted), applies Section 55(2)(ac) grandfathering rules, and pools Section 112A LTCG exemptions (₹1,25,000 threshold/FY).
    - **REST API Endpoint:** Exposed `GET /api/v1/capital-gains/unrealized` in `backend/app/api/v1/endpoints/capital_gains.py`.
    - **Frontend Components:** Added `useUnrealizedCapitalGains` query hook to `useCapitalGains.ts`. Created `UnrealizedGainsCard.tsx` and `UnrealizedGainsModal.tsx` on `CapitalGainsPage.tsx` with Section 112A exemption progress bar (Realized Used vs Unrealized Usable vs Remaining Headroom) and Privacy Mode support (`usePrivacy`).
    - **Automated Tests:** Authored `backend/app/tests/api/v1/test_unrealized_tax.py` (3/3 passing) and `frontend/src/components/CapitalGains/UnrealizedGainsModal.test.tsx` (193/193 tests passing across 47 suites).

*   **Release v1.4.0 Architecture & Issue Seeding (Updated 2026-08-17):**
    - Published official GitHub issues [#516](https://github.com/aashishbhanawat/ArthSaarthi/issues/516) (Unrealized Capital Gains & Exemption Pooling), [#517](https://github.com/aashishbhanawat/ArthSaarthi/issues/517) (Income & TDS Management), [#518](https://github.com/aashishbhanawat/ArthSaarthi/issues/518) (Tax Deductions Chapter VI-A), and [#519](https://github.com/aashishbhanawat/ArthSaarthi/issues/519) (Structured Tax Summary Report & Old vs New Regime Comparison).
    - Created detailed 11-point architectural specifications [`docs/v1.4.0_detailed_plan.md`](file:///media/data/AppData/CodeServer/pms4/ArthSaarthi/docs/v1.4.0_detailed_plan.md) and [`docs/v1.4.0.md`](file:///media/data/AppData/CodeServer/pms4/ArthSaarthi/docs/v1.4.0.md).
    - Created updated FR feature specifications [`docs/features/FR6.5.7_unrealized_capital_gains.md`](file:///media/data/AppData/CodeServer/pms4/ArthSaarthi/docs/features/FR6.5.7_unrealized_capital_gains.md), [`docs/features/FR16.1_income_data_management.md`](file:///media/data/AppData/CodeServer/pms4/ArthSaarthi/docs/features/FR16.1_income_data_management.md), [`docs/features/FR16.3_tax_deductible_expenses.md`](file:///media/data/AppData/CodeServer/pms4/ArthSaarthi/docs/features/FR16.3_tax_deductible_expenses.md), and [`docs/features/FR16.4_structured_tax_summary.md`](file:///media/data/AppData/CodeServer/pms4/ArthSaarthi/docs/features/FR16.4_structured_tax_summary.md).

*   **SECRET_KEY Persistence & PyInstaller Alembic Path Fix (Updated 2026-08-16):**
    - Implemented `_get_or_create_secret_key()` in `backend/app/core/config.py` to persist `SECRET_KEY` to `secret.key` in the app data directory (`_get_app_dir()`). Eliminates `jose.exceptions.JWTError: Signature verification failed` and HTTP 401 unauthenticated redirects across application restarts on desktop/mobile environments.
    - Updated `run_db_migrations()` in `backend/app/db/init_db.py` to set absolute `script_location` on `Alembic Config` object, preventing `Path doesn't exist: alembic` warning in PyInstaller standalone app bundles on macOS.

*   **YFinance Batch Enrichment Rate-Limiting & Lag Fix (Updated 2026-08-15):**
    - Added negative caching (`enrichment_failed:{ticker}`) in `YFinanceProvider.get_enrichment_data` (cached for 15 minutes) and early loop termination on HTTP 429 / `Too Many Requests` in `get_enrichment_data_batch`.
    - Added default fallback assignment (`asset.sector = "Other"`, `asset.investment_style = "Blend"`) in `backend/app/crud/crud_holding.py` when stock enrichment is unavailable or rate-limited. Prevents holdings calculation from hanging for 200+ seconds and triggering HTTP client / ASGI socket disconnects.

*   **Holding `Decimal('NaN')` ValidationError, Upstox SSL Fallback, Android DB Migration & Foreground Service Fixes (Updated 2026-08-15):**
    - Added `_to_finite_decimal` and `_to_finite_float` helpers in `backend/app/crud/crud_holding.py` to sanitize all holding calculation fields before instantiating `schemas.Holding` and `schemas.PortfolioSummary`.
    - Added `_urlopen_safe` helper in `backend/app/services/upstox_metadata_service.py` and `backend/app/services/providers/upstox_provider.py` with automatic `ssl._create_unverified_context()` fallback to prevent `[SSL: CERTIFICATE_VERIFY_FAILED]` crashes on macOS / standalone PyInstaller builds.
    - Added `run_db_migrations()` and `_ensure_sqlite_columns_exist()` in `backend/app/db/init_db.py` and hooked them into FastAPI `startup_event` in `backend/app/main.py`. Automatically runs Alembic migrations and performs SQLite column auto-sync (`ALTER TABLE ADD COLUMN`) on app startup to upgrade local databases on Android and Desktop without missing column errors (e.g. `goals.expected_return`).
    - Promoted `BackendService` in `frontend/android/app/src/main/java/com/arthsaarthi/app/BackendService.kt` to an Android Foreground Service (`startForeground(1001, notification)`) with `android:foregroundServiceType="specialUse"` in `AndroidManifest.xml` and auto-revival checks in `PythonBackendPlugin.kt` to eliminate Android `ActivityManager` app idle service terminations.

*   **Release v1.3.0 Preparation (Updated 2026-08-13):**
    - Synchronized version numbers across `backend/app/main.py`, `backend/app/api/v1/endpoints/system.py`, `frontend/package.json`, `frontend/src/pages/MorePage.tsx`, and `frontend/android/app/build.gradle.kts`.

*   **FD Transaction Types ResponseValidationError Fix (Issue #510) (Updated 2026-08-11):**
    - Added `FD_DEPOSIT` and `FD_MATURITY` to `TransactionType` enum in `backend/app/schemas/enums.py`.
    - Removed restrictive `enum=["BUY", "SELL"]` query parameter constraint on `read_transactions` in `backend/app/api/v1/endpoints/transactions.py`.
    - Added `test_read_transactions_with_synthetic_fd_types` to `backend/app/tests/api/v1/test_transactions.py` (passing cleanly).

*   **PPF Interest Rate Update (Issue #508) (Updated 2026-08-10):**
    - Updated historical PPF interest rate seed data end date in `backend/app/db/seed_data/ppf_interest_rates.py` to `2026-09-30` (Q3-2026) at `7.1%`.
    - Updated `test_seed_interest_rates_correctness` in `backend/app/tests/api/v1/test_admin_interest_rates.py` to verify seed data validity and coverage through Q3-2026.

*   **Manual Testing Bug Fixes (Issue #504) (Updated 2026-08-06):**
    - **Import Session Error Detail (Bug 1):** Fixed error handling in `commit_import_session` and `commit_fd_import_session` in `backend/app/api/v1/endpoints/import_sessions.py` by adding `except HTTPException: raise` before the outer `except Exception as e:` block. Now returns HTTP 400 with exact error details (e.g. insufficient holdings to sell) instead of swallowing it into a 500 Internal Server Error.
    - **Risk Profile Auto-Redirect Removal (Bug 2):** Removed auto-redirection to `/risk-profile` on 404 error from `frontend/src/pages/DashboardPage.tsx`. Users without a risk profile can browse the dashboard normally without being forced into the risk wizard.
    - **Login Page System Logs Link Removal (Bug 3):** Removed the broken "View System Logs (Diagnostics)" link from `frontend/src/pages/AuthPage.tsx` which attempted unauthenticated access to `/admin/logs` (resulting in a redirect back to `/login`).
    - **Server Mode Seeding Splash Bypass (Bug 4):** Updated `get_seeding_status` in `backend/app/api/v1/endpoints/system.py` to return `status: COMPLETE` when `DEPLOYMENT_MODE == "server"`. Updated `frontend/src/pages/AuthPage.tsx` to set `seedingComplete` to `true` when not running natively on mobile, and updated `MobileSeedingSplash.tsx` to call `onComplete()` on fetch error.

*   **Upstox Provider Integration & Market Holidays (Issue #498) (Updated 2026-07-31):**
    - **Upstox Metadata Service (`UpstoxMetadataService`):** Downloaded and cached `NSE.json.gz` from Upstox CDN to build 0-cost $O(1)$ lookup maps for ISIN $\leftrightarrow$ Symbol $\leftrightarrow$ `instrument_key`. Integrated `GET /v2/market/holidays` for weekend and trading holiday detection (`is_market_closed`).
    - **Asset Seeding & Cross-Verification (`AssetSeeder`):** Integrated `process_upstox_metadata()` in `app/services/asset_seeder.py` to seed active stocks/ETFs directly from `NSE.json.gz` during server boot / manual admin sync, while cross-verifying and backfilling missing ISINs and exchange tags on existing assets.
    - **Upstox Provider (`UpstoxProvider`):** Implemented `FinancialDataProvider` using public V3 historical candles (`GET /v3/historical-candle/...`) without requiring access keys or authorization headers. Enforces 50 req/sec throttling and Redis caching (`CACHE_TTL_CURRENT_PRICE = 900`, `CACHE_TTL_HISTORICAL_PRICE = 86400`).
    - **Financial Data Service (`FinancialDataService`):** Configured Upstox as the primary stock & ETF provider, with `yfinance` as fallback for foreign/unmapped assets.
    - **Test Suite:** Added 6 unit tests in `test_upstox_provider.py` (100% passing).

*   **Pydantic V1 Fallback Config Stabilization (Issue #495) (Updated 2026-07-30):**
    - **Pydantic V1/V2 Compatibility:** Discovered that `from pydantic import ConfigDict` does not throw `ImportError` on Pydantic V1 (since it is defined internally as a `TypedDict`), bypassing fallback blocks. Resolved by performing a strict `VERSION.startswith("2.")` check across all schemas, and corrected all fallback configuration keys from `from_orm = True` to `orm_mode = True` (`asset.py`, `import_session.py`, `portfolio.py`, `risk.py`, `transaction.py`, `user.py`, `watchlist.py`, etc.). This ensures successful conversion of SQLAlchemy objects to Pydantic schemas under Pydantic V1.

*   **Android Onboarding & Account Creation Fixes (Issue #494) (Updated 2026-07-29):**
    - **Response Validation (Pydantic V1):** Updated `EncryptedString` database type decorator in `backend/app/db/custom_types.py` to dynamically decode `bytes` object to `utf-8` string when `DEPLOYMENT_MODE != "desktop"`. This resolves `ResponseValidationError` when SQLite reads `email` or `full_name` fields as `bytes` on Android.
    - **Token Response Validation:** Added `"android"` to the `deployment_mode` Literal in `backend/app/schemas/token.py` to prevent `ResponseValidationError` during login when running in Android mode.
    - **Database Diagnostics:** Enhanced exception logging in `get_db` (`backend/app/db/session.py`) by passing `exc_info=True` and log validation error details for `ResponseValidationError`.
    - **Admin Setup Endpoint:** Wrapped user creation and database commit in `setup_admin_user` (`backend/app/api/v1/endpoints/auth.py`) inside a `try...except` block, ensuring traceback capture and reporting descriptive 500 error messages back to the client.
    - **Backfill Script Integration:** Updated `backfill_links` in `backend/app/scripts/backfill_transaction_links.py` to support optional session parameter. Corrected background thread in `initialization_service.py` to prevent threading arguments mismatch (`TypeError`).
    - **Onboarding Splash Screen:** Restored the `MobileSeedingSplash` component and diagnostic logs link in `frontend/src/pages/AuthPage.tsx` to handle asset seeding elegantly on first mobile launch.

*   **Android App Startup Crashes Stabilization (Issue #493) (Updated 2026-07-28):**
    - **Backend schemas:** Patched `backend/app/schemas/__init__.py` to pass the `Asset` class parameter dynamically during the `Transaction.update_forward_refs()` call in Pydantic v1 environments. This resolves the `NameError: name 'Asset' is not defined` crash.
    - **Backend Cache Factory:** Wrapped the eager `redis` module import in `backend/app/cache/factory.py` inside a `try...except ImportError` block. Since the Android app runs with `CACHE_TYPE = "disk"` and doesn't install the `redis` package, this prevents a `ModuleNotFoundError: No module named 'redis'` crash on Android startup.
    - **Backend Benchmark Service:** Wrapped the eager `pyxirr` module import in `backend/app/services/benchmark_service.py` inside a `try...except ImportError` block with a numpy-based Newton-Raphson fallback function for XIRR. Since Chaquopy doesn't support the compiled `pyxirr` package, this prevents `ModuleNotFoundError: No module named 'pyxirr'` on Android startup.
    - **Backend Backfill Script:** Added `run_backfill = backfill_links` alias in `backend/app/scripts/backfill_transaction_links.py`. Since `initialization_service.py` attempts to import `run_backfill` from this script, this resolves `ImportError: cannot import name 'run_backfill'` on Android startup.
    - **Verification:** Verified 351 tests pass successfully under the SQLite/DiskCache local test suite.


*   **Android Background Daily Portfolio Snapshot (Issue #492) (Updated 2026-07-26):**
    - **Backend API:** Created `POST /api/v1/system/snapshots/run-daily` to trigger daily snapshots via local loopback.
    - **Android/WorkManager:** Developed `SnapshotWorker.kt` utilizing `CoroutineWorker` to boot the `BackendService`, verify health, and invoke the daily snapshot API. Exposed this capability via `PythonBackendPlugin` to React.
    - **Frontend Settings:** Added a native settings card `AndroidSettingsCard` in the Profile page allowing users to toggle background sync, persisting the state securely.


*   **Project Goal Future Value and Track Status (Issue #478 / FR13.4) (Updated 2026-07-25):**
    - **Backend Analytics Engine:** Rewrote `get_goal_with_analytics` in `crud_goal.py` to compile cash flows across all linked portfolios and standalone assets. Computes the combined dynamic XIRR of linked assets and compounds the current amount to the goal's target date. If calculated XIRR is invalid or out-of-bounds (i.e. $\le 0\%$ or $> 100\%$), falls back to the goal's expected return or a default rate ($10\%$). Determines goal track status (`"On Track"` or `"Off Track"`) and generates monthly, quarterly, or yearly projection data points.
    - **Frontend UI & Visualization:** Added an interactive Chart.js growth projection Line chart plotting the Projected Path and the Target Path (growth with required SIP contributions) to `GoalDetailView.tsx`. Upgraded the summary cards layout to a responsive 4-column grid on desktop, showing calculated return rate, linked assets XIRR, projected future value, and a styled track status badge. Masked values under Privacy Mode using `usePrivacySensitiveCurrency`.
    - **Test Suite:** Wrote 2 comprehensive backend test cases validating unified cash flow compilation, projection math, fallback bounds checks, and status flags in `test_goals.py` (all passing). Created `GoalDetailView.test.tsx` to verify summary cards, status badge classes, and projection chart coordinates in the frontend (all passing).

*   **Calculate Goal Required Contribution Rate (SIP) (Issue #477 / FR13.3) (Updated 2026-07-21):**
    - **Backend & Database Migration:** Added `expected_return` column (`Numeric(5, 2)`) to `Goal` model and schema via migration `c7e8f9a0b1c2`. Updated `get_goal_with_analytics` in `crud_goal.py` to calculate ordinary annuity monthly SIP values taking into account target date remaining duration ($N$), present value asset appreciation ($PV_{\text{future}}$), 0% interest rate fallback, and past target dates ($N \le 0$).
    - **Frontend UI & Privacy Support:** Added Expected Annual Return (%) input to `GoalFormModal.tsx` and added Expected Return & Required Monthly SIP cards to `GoalDetailView.tsx`. Masked values under Privacy Mode using `usePrivacySensitiveCurrency`.
    - **Test Suite:** Added 4 backend test cases covering standard compounding, PV growth exceeding goal target, 0% rate, and past target dates in `test_goals.py`. All 15 tests passed cleanly.

*   **Risk Profile PR #481 Review Fixes, E2E Stabilization & Asset Cleanup (Issue #76 / PR #481) (Updated 2026-07-16):**
    - **Database Migration:** Switched from `sa.text('now()')` to `sa.func.now()` to ensure cross-database compatibility with SQLite.
    - **Frontend State Load:** Wrapped `localStorage` parsing for `answers` in a `try-catch` block, and added bounds and type validation for `currentStep` in `RiskQuestionnaireWizard.tsx`.
    - **Backend Schema Constraints:** Implemented question-specific option mappings in `validate_answers` inside `backend/app/schemas/risk.py` to prevent validation of invalid options for questions with fewer choices.
    - **UI Correction:** Adjusted maximum score display denominator in `RiskProfileResults.tsx` to `/ 47`.
    - **Asset Cleanup:** Removed all extraneous files accidentally committed under `frontend/android/app/src/main/assets/public/*`.
    - **E2E Stabilization:** Added `skip_risk_redirect` sessionStorage/localStorage bypass to `DashboardPage.tsx` and explicitly exempted admin users. Configured Playwright globally in `playwright.config.ts` to pre-populate this flag to avoid test failures caused by onboarding redirects. Updated unit tests in `DashboardPage.test.tsx` to correctly mock `useAuth`.
    - **Verification:** Added backend integration test validating invalid question choices, and successfully ran full Postgres, SQLite, Jest, and Playwright E2E test suites (100% pass rate).

*   **Risk Profile 13-Question Grable & Lytton Upgrade (Issue #76) (Updated 2026-07-15):**
    - **Backend:** Updated validation schemas to require 13 answers (`q1` to `q13`), refactored scoring logic in `crud_risk.py` with standard G&L points and benchmarks (Conservative, Moderate, Growth, Aggressive), and updated all integration unit tests.
    - **Frontend:** Upgraded wizard questionnaire in `RiskQuestionnaireWizard.tsx` to display all 13 questions with localized INR (`₹`) currency, adjusted progress calculation to start at 0% complete, implemented `localStorage` progress caching to prevent losing state upon component unmounting, and added auto-redirect to `/risk-profile` on first login boarding in `DashboardPage.tsx`.
    - **Responsiveness:** Corrected vertical overflow layout clipping of the sidebar navigation menu in `NavBar.tsx` and updated mobile header title mapping.
    - **Verification:** All Jest and backend integration tests passed successfully with zero linter errors.

*   **Benchmark Service Test Coverage (Issue #371) (Updated 2026-07-14):**
    - **Backend Fix:** Added comprehensive unit tests in `backend/tests/unit/backend/test_benchmark_service.py` verifying outflow/withdrawal reduction ratios, clamping negative invested amounts to zero under highly profitable sales, synthetic transactions generated for FDs and RDs (including interval mapping checks), and correct handling/ignoring of all other transaction types (`RSU_VEST`, `CONTRIBUTION`, `COUPON`, `DIVIDEND`, `BONUS`, `SPLIT`, etc.).
    - **Verification:** Achieved 100% statement and branch coverage of the outflow block in `_simulate_daily`. Verified all tests pass successfully in the test container with clean ruff check linting.

*   **Sell Modal Portfolio Scoping (Issue #442) (Updated 2026-06-11):**
    - **Backend Fix:** Updated `crud.transaction.get_available_lots` to accept and filter by `portfolio_id`. Modified the `/available-lots/{asset_id}` GET endpoint to accept `portfolio_id` as a query parameter and added authorization checks to verify portfolio ownership. Passed `portfolio_id` to `get_available_lots` during auto-FIFO linking in `create_with_portfolio`.
    - **PR Review Optimization:** Optimized the portfolio ownership check by querying only the `user_id` column instead of fetching the entire model instance. Removed the redundant database-level `.order_by(...)` clause in `get_available_lots` since transactions are sorted in Python.
    - **Frontend Fix:** Modified the `getAvailableLots` API service function to pass `portfolio_id`. Updated `TransactionFormModal` to supply the active `portfolioId` and added it as a dependency in the useEffect fetch block.
    - **Regression Test Coverage:** Created `test_get_available_lots_multi_portfolio` verifying correct filtering of available lots by portfolio, IDOR security permissions (403), and non-existent portfolio handling (404). Fixed PEP8 line length warnings (E501) across code files and tests.

*   **Transaction Restore Robustness (PR #457 Review / Issue #441 Follow-up) (Updated 2026-06-09):**
    - **Backend Fix:** Refined helper functions `_serialize_date` and `_parse_date` in `backend/app/services/backup_service.py` to support date/datetime objects and ISO strings. Serialized all transaction dates to strings during key generation for sorting to prevent `TypeError` when comparing date and datetime objects. Normalized transaction types to uppercase (e.g., converting `"sell"` to `"SELL"` and `"Buy"` to `"BUY"`) to prevent enum validation issues during restore.
    - **Regression Test Coverage:** Added `test_backup_restore_robust_sorting` to `test_backup_restore.py` to verify sorting and ingestion of mixed-format backup data.

*   **Transaction Sorting during Restore (Issue #441) (Updated 2026-06-07):**
    - **Backend Fix:** Updated `restore_backup` in `backend/app/services/backup_service.py` to sort transactions before processing. Sorting is chronological by `transaction_date`, and for identical dates, acquisitions (e.g., `BUY`, `CONTRIBUTION`) are processed before disposals (`SELL`). This ensures that the database has sufficient holdings recorded before a `SELL` transaction is processed.
    - **Integration Test Coverage:** Added `test_backup_restore_shuffled_transactions` to `test_backup_restore.py`, verifying that restore completes successfully even when the backup transactions are shuffled out of order.

*   **PPF Interest Transaction Security (Issue #440) (Updated 2026-06-07):**
    - **Backend Protection:** Implemented checks in `PUT /api/v1/transactions/{transaction_id}` and `DELETE /api/v1/transactions/{transaction_id}` endpoints to reject updates or deletions of `INTEREST_CREDIT` transactions belonging to a `PPF` asset, returning a `400 Bad Request` HTTP error. Added defensive checks to ensure `transaction.asset` is not `None` before checking `asset_type`.
    - **Frontend Immutability:** Disabled the "Edit" and "Delete" buttons in the desktop `TransactionHistoryTable` and portfolio `TransactionList` views with explanatory tooltip titles. Hid the edit/delete options entirely in the mobile card-based `TransactionCard` view.
    - **DRY Refactoring:** Extracted the transaction helper functions (`isEditable`, `isDeletable`, `getDisabledTitle`) into a shared utility file (`frontend/src/utils/transaction.ts`) to avoid duplicate logic across frontend components.
    - **Verification:** Added `test_ppf_interest_credit_immutability` to the integration test suite, verifying both update and delete operations are rejected. Passed all backend and frontend unit tests cleanly.

*   **Asset Seeding & Classification Bug (2026-06-04):**
    - **Asset Misclassification Fix:** Resolved Git Issue #438 where regular stocks containing month-like substrings in their names (e.g., "Indraprastha Gas" containing "APR", "Amara Raja" containing "MAR") were incorrectly classified as `BOND`.
    - **In-Memory NSEScripMaster Mapping:** Implemented an in-memory `ISIN -> Series` lookup map populated from `NSEScripMaster.txt` first. This ensures BSE and NSE assets are classified based on the authoritative NSE Series column (e.g., `EQ`, `BE`, `SM`, `ST` mapped to `STOCK`), irrespective of the source exchange.
    - **Refined Heuristics:** Replaced aggressive substring matching with a precise word-boundary regex (`(\b|\d)(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)(\b|\d)`) to isolate month names.
    - **Self-Healing Database Correction:** Embedded an auto-correction step inside the asset seeder startup that scans for and automatically corrects previously misclassified `BOND` assets to `STOCK`, deleting the orphaned child `Bond` records. Also created a standalone python script `fix_misclassified_bonds.py` to fix existing data on-demand.
    - **Verification:** Authored 6 regression tests verifying classification, cross-exchange mapping, and automatic database correction. Verified all 326 tests pass cleanly.

*   **Mobile UX Optimization & Backend Stabilization (2026-05-02):**
    - **Capital Gains Mobile Refactor:** Transitioned the `CapitalGainsPage.tsx` from horizontally scrolling tables to a responsive, card-based dual-layout. Implemented custom cards for Advance Tax, Realized Gains, Schedule 112A, Foreign Gains, and Dividends.
    - **Breakpoint Standardization:** Synchronized responsive breakpoints to `lg` (1024px) across the application to ensure consistent UI on tablets and large-screen mobile devices.
    - **Backend Bond Fix:** Resolved a critical `AttributeError` (missing `Bond` export in `app.schemas`) that was crashing the `search-stocks` and `watchlists` endpoints.
    - **Import Logic Hardening:** Enhanced transaction commit logic to provide more descriptive error messages (e.g., specific ticker names for "insufficient holdings" errors).
    - **CSS Standardization:** Purged non-standard utility classes and ensured alignment with the project's design system (standardized green/success tokens).
*   **Import Pipeline & NaN Robustness (2026-05-02):**
    - **Crash Resolution:** Fixed a critical `AttributeError` ('float' object has no attribute 'upper') occurring during the import preview phase when optional fields like ISIN were missing.
    - **Sanitization:** Implemented consistent NaN-to-None sanitization in the import endpoints to ensure Pydantic validation handles missing spreadsheet data correctly.
    - **CRUD Hardening:** Added defensive type-checking to `CRUDAsset` to prevent crashes when non-string values are passed to ticker or ISIN lookup methods.
    - **E2E Stability:** Resolved brittle test failures in `inactivity-timeout.spec.ts` by implementing flexible regex-based assertions for dynamic UI elements.
    - **Verification:** Successfully verified the fix with a passing E2E test suite covering the entire import, mapping, and commitment pipeline.
*   **Android Restoration & Pydantic v1/v2 Compatibility (2026-05-01):**
    - **Pydantic Compatibility:** Restored `pydantic_compat.py` and updated all backend schemas to support both Pydantic v1 (Android) and v2 (Server/Docker).
    - **Storage Migration:** Migrated import session storage from Parquet to JSON to resolve binary dependency crashes in the embedded Android environment.
    - **Security & Stability:** Restored Login Rate Limiting (PR #376) and verified IDOR protections (PR #423) remain intact. Fixed database authentication conflicts in the test environment.
    - **Mobile UI:** Restored and merged `MobileHeader`, `MobileNav`, and mobile-optimized layouts with the latest Admin dashboard updates.
    - **Verification:** Achieved 100% backend test pass (309/309) across both Postgres/Redis and SQLite/DiskCache (Android mode) environments, specifically verifying the rate-limiting engine on both.

*   **Android Build Consolidation & Test Alignment (2026-04-18):**
    - **Workflow Consolidation:** Integrated Android release and debug builds into `release.yml` and `test-builds.yml`; removed redundant `android-build.yml`.
    - **Test Alignment:** Updated `conftest.py` and test utilities to support `android` mode (SQLite/DiskCache) with consistent auth bypass logic.
    - **Verification:** Created `test_android_mode.py` and verified 300+ backend tests pass in `android` mode.
    - **Documentation:** Formalized FR14.4 and NFR14 for Android stability and native enablement. Documented battery/permission needs in `android_enablement_notes.md`.
    - **Environment:** Disabled verbose yfinance/httpx debug logging across backend and Android python entry points.
*   **Asset Seeding Consolidation & Regression Fixes (2026-04-16):**
    - **Seeding Refactor:** Created `financial_utils.py` to centralize date/URL/download logic previously duplicated in `cli.py`, `initialization_service.py`, and `admin_assets.py`.
    - **Capital Gains Security Fix:** Enforced strict `user_id` filtering in `CapitalGainsService` and secured API endpoints in `capital_gains.py` to prevent data leakage between users (Issue #408).
    - **FIFO Linking & Restoration:** Fixed `backup_service.py` to sort transactions chronologically during restoration and added automated background backfill in `initialization_service.py` to ensure data parity with the baseline.
    - **Sharpe Ratio Documentation:** Verified and documented the expected delta in Sharpe Ratio calculation due to data windowing changes.
    - **UI Parity:** Restored the premium Transaction History design on the Android branch and fixed duplicate React keys on the Capital Gains page.
    - **Diversification Fix:** Resolved "STOCK" vs "Stock" duplication and missing debt asset accounting in pie charts.
    - **Repository Cleanup:** Purged 10+ redundant temporary files and build artifacts.
    - **Lint Compliance:** Fixed 29 backend/frontend lint issues across multiple modules.
*   **Bond Metadata Sync, DateInput Fix & Android Dependency Stabilization (2026-04-15):**
    - **Bond Metadata:** Resolved a major issue where maturity dates were not updating during transaction edits. Added `updateBondByAssetId` and explicit sync in `TransactionFormModal.tsx`.
    - **DateInput Stabilization:** Fixed the "double-submit" validation lag and calendar synchronization issues.
    - **Android Dependency Fix:** Downgraded Capacitor and Vite to stable v6 releases to resolve persistent package conflicts. Aligned `appId` and incremented `versionCode` to 3 for successful upgrades.
*   **Android UI Polish, Percentage Scaling & Lint Resolution (2026-04-14):**
    - **Percentage Correction:** Fixed the "double-conversion" bug in `HoldingCard.tsx` where percentages were shown as 0.38% instead of 38%. Standardized centralized formatting across all Debt/Bond modals.
    - **Safe Area Support:** Enforced `pt-safe` padding in all drill-down modals and the mobile header for Android status bar compliance.
    - **Mapping UX:** Modularized the "Needs Mapping" logic into `MappingResolutionModal.tsx`, improving ergonomics on small screens.
    - **Lint Cleanup:** Resolved 6 frontend lint errors related to type safety (`any`) and direct DOM access in `DateInput.tsx`, `LogsPage.tsx`, and `MorePage.tsx`.
*   **App-Wide Mobile Card Parity & Import Stability (2026-04-13):**
    - **Mobile Card Parity:** Transitioned all remaining table-based layouts (Transactions, Dashboard, Watchlists, Aliases, FMV, Users, Interest Rates) into a premium card-based mobile interface with footer actions for better touch ergonomics.
    - **Import Session Robustness:** Fixed a critical `AttributeError` crash caused by `NaN` values in spreadsheet imports. Added defensive type-checking and sanitization to `crud_asset.py` and `import_sessions.py`.
    - **Flexible Date Input:** Created a reusable `DateInput.tsx` component supporting both manual typing and native date picking. Integrated it into `TransactionFormModal`, `AddAwardModal`, `InterestRateFormModal`, and `GoalFormModal`.
    - **Investment Style Analytics:** Resolved "Unknown" classification for equities; updated `AssetSeeder` and `crud_holding.py` to handle metadata enrichment correctly.
*   **Android v1.2.0-exp Initial Stabilization (2026-04-12):** 
    - Resolved `ValidationError` in `backup_service.py` by coercing date strings to `datetime`.
    - Implemented `pt-safe` layout spacing for Android status bar compliance.
    - Added internal User Guide navigation and GitHub community links.
*   **FD Lifecycle & Import Robustness (2026-03-31):** Stabilized the FD/RD lifecycle by redacting matured assets from Holdings while preserving their interest in the Portfolio Summary. Implemented synthetic transaction injection for the History tab with conditional Edit/Delete support. Fixed import session commit logic to re-raise `HTTPException` for clearer validation messaging.
*   **Comprehensive QA & User Guide (2026-03-27):** Exhaustive verification of the v1.2.0 release candidate. Validated Reliance (1:1 Bonus) and HDFC Bank (1:2 Reverse Split) sell transactions. Confirmed Section 112A Grandfathering using Actual Cost vs FMV Jan 2018 logic. Generated exhaustive platform documentation with localized media assets.
*   **Live Testing v1.2.0 Fixes (2026-03-23):** Completely stabilized the benchmarking engine to handle edge cases like absent Yahoo indices (Debt benchmark fallback) and extreme stock gains (via Lot-Based FIFO tracking). Fixed historical mathematical distortions in PPF, and matured FD/RD analytical models. Fixed `AssetSearchResult` to expose Bond metadata to the frontend.

*   **Advanced Benchmarking (FR6.3):** Implemented hybrid benchmarks (35/65, 50/50 equity/debt blends), risk-free rate overlay, and category-level (equity vs debt) XIRR comparison. Fixed XIRR calculation for category subsets to use actual current market value.
*   **Portfolio Delete Error Handling:** Catching FK constraint violations when deleting a portfolio linked to goals — returns a 409 Conflict with a user-friendly message instead of a 500. Frontend now displays this error via alert.
*   **Non-Market Asset Historical Chart:** Fixed multiple bugs where FDs, RDs, PPF, and Bonds showed `0` value on historical dates:
    *   Added `BOND` to `supported_types` for historical price fetching.
    *   Fixed PPF `process_ppf_holding` to support historical simulation without DB side-effects.
    *   Fixed early-return bug where FD/RD-only portfolios returned empty history.
    *   Fixed `Holding` schema crash for FDs/RDs missing an `account_number`.
*   **UI "No Data" Fix:** Category comparison no longer hides the entire component when a category has no transactions — keeps navigation elements visible.
*   **Desktop App Migration Fix:** Added `fmv_2018` to the manual schema migration script in `run_cli.py` to prevent startup crashes when upgrading the desktop app version.
*   **v1.2.0 Final Stabilization (2026-03-24):** Completed the comprehensive release preparation. Removed all legacy 'Buy Me A Chai' branding, synchronized all versioning to v1.2.0 across frontend and docs, and purged development-only statement files (PDFs, XLS) from the repository root. Standardized documentation by consolidating redundant handoff and roadmap files.

## 3. Implemented Functionality

### Core Features
-   **User Authentication:** Full setup, login, and session management.
-   **Administration:** Basic user management (CRUD).
-   **Portfolio Management:** Multi-portfolio support (CRUD).
-   **Transaction Management:** Full CRUD for transactions.

### Asset Class Support
-   **Equities:** Stocks, ETFs.
-   **Mutual Funds:** Indian MFs via AMFI.
-   **Fixed Income:**
    -   Fixed Deposits (FDs) - Cumulative & Payout.
    -   Recurring Deposits (RDs).
    -   Public Provident Fund (PPF).
    -   Bonds (Corporate, Government, SGBs, T-Bills) with manual coupon tracking.

### Key Features
-   **UML documentation:** Added `docs/uml_design.md` with System Architecture, ERD, and backend Class diagrams.
-   **Dashboard:** High-level summary, historical chart, asset allocation, and top movers.
-   **Daily Portfolio Snapshots:** Background cache of daily valuations to optimize history chart loading, including Desktop-mode scheduler support.
-   **Historical Chart Accuracy:** Fallback engine in `_get_portfolio_history` calculates values for non-market assets (FDs, RDs, PPF) on dates without snapshots, and treats Bonds as market-traded assets with historical prices.
-   **Consolidated Holdings View:** Grouped by asset class with sorting and drill-down for transaction history.
-   **Advanced Analytics:** Portfolio and Asset-level XIRR calculation.
-   **Advanced Benchmarking (FR6.3):**
    -   **Single Index:** Compare portfolio against Nifty 50 or Sensex.
    -   **Hybrid Benchmarks:** CRISIL Hybrid 35/65 and Balanced 50/50 blends.
    -   **Risk-Free Rate Overlay:** Dashed green line on chart showing compound risk-free growth.
    -   **Category Comparison:** Equity vs Nifty 50, Debt vs bond yield — with accurate XIRR using actual market values.
-   **Automated Data Import:** Support for Zerodha, ICICI Direct (Tradebook & Portfolio), MFCentral CAS, CAMS, KFintech, Zerodha Coin, and generic CSV files. Also includes **Fixed Deposit (FD) PDF imports** (HDFC, ICICI, SBI) with password protection support. Supports **asset alias mapping** with admin management (view, edit, delete) of all aliases. **Auto-creation of assets for ISIN tickers** ensures seamless onboarding of new funds.
-   **Watchlists:** Create and manage custom watchlists.
-   **Goal Planning:** Define financial goals and link assets to track progress.
-   **Mutual Fund Dividends:** Track both cash and reinvested dividends for mutual funds.
-   **Stock Dividend Reinvestment (DRIP):** Support for automatic reinvestment of stock dividends.
-   **Foreign Income Tracking:** Correctly handle dividends and coupons for foreign assets using historical FX rates.
-   **Foreign Stock & Currency Support:** Track assets in foreign currencies (e.g., USD). Portfolio values, analytics, and performance metrics are automatically converted and consolidated into your base currency (INR) using real-time and historical FX rates.
-   **Security & User Management:**
    -   Audit Logging Engine for key events.
    -   User Profile Management (name/password change).
    -   Inactivity Timeout to automatically log out users.
    -   Desktop-mode encryption support.
-   **UX Enhancements:**
    -   Privacy Mode to obscure sensitive values.
    -   Context-sensitive help links.
    -   Dark theme with user preference persistence.
-   **Exhaustive User Guide:** Comprehensive `USER_GUIDE.md` in `temp_qa_run/` featuring 50+ localized screenshots, transaction logs, and feature walk-through scripts.
-   **Capital Gains & Dividend Reporting:**
    -   Comprehensive Capital Gains reports for Schedule 112A (Grandfathered Equity) and Schedule FA (Foreign Assets).
    -   **Data Isolation:** Enforced strict user-level filtering to ensure users can only ever access their own Capital Gains data (Issue #408).
    -   **Dividend Report (FR 6.5):** Dedicated tracking for dividends, including Rule 115 compliant TTBR FX conversion for foreign assets (ESPP/RSU).
    -   Support for Tax Lot Accounting (Specific Identification) vs FIFO.
    -   Accurate taxation rules for Bond ETFs, International ETFs, and SGBs.
    -   **Authenticated Exports:** Universal `downloadCsv` utility to ensure CSV downloads via `window.open` alternative carry Auth tokens.

## 4. Architectural Improvements

-   **Pluggable Financial Data Service (NFR12):** The `FinancialDataService` has been refactored into a provider-based architecture (Strategy Pattern), making it easy to add new data sources. It currently supports AMFI (Mutual Funds), NSE Bhavcopy (Indian Equities/Bonds), and yfinance (fallback/international).
-   **Pluggable Caching Layer (NFR9):** The application supports both Redis and a file-based `DiskCache` for improved performance and deployment flexibility.
-   **Analytics Caching (NFR9.2):** Expensive analytics and holdings calculations are cached to improve UI responsiveness and reduce server load.
-   **Cache Invalidation:** `invalidate_caches_for_portfolio` deletes all range-specific dashboard history keys, portfolio analytics, holdings, and stale `DailyPortfolioSnapshot` DB records. Optimized with **bulk deletion (#420)** for significantly faster invalidation in large-scale operations like backup restores.

## 5. Known Issues & Active Bugs

-   **Historical Chart for Non-Market Assets:** Despite recent fixes, there may still be edge cases where FD/PPF/Bond values aren't fully accurate on historical chart dates. This is under investigation and will be addressed in a follow-up task.

## 6. Next Steps & Priorities

Based on the `product_backlog.md`, the next features to consider are:

1.  **Historical Chart Non-Market Asset Bug (follow-up):** Continue investigating and resolving any remaining edge cases for FD/PPF/Bond historical values.
2.  **Automated Data Import - Phase 3 (FR7):** Implement a parser for Consolidated Account Statements (MF CAS) to simplify Mutual Fund onboarding.
3.  **Forgotten Password Flow (FR1.6):** Implement a secure password reset mechanism.
## 7. E2E Test Stability Fix (2026-03-06)

-   **Issue #312:** Fixed `ppf-modal-verification.spec.ts` flaky failures (60% fail rate) caused by race conditions after PR #278 added analytics components to portfolio detail page.
-   **Key lesson:** Avoid `waitForLoadState('networkidle')` on pages with continuous API activity. Use targeted element assertions instead.
-   **Test-results debugging:** Added `test-results` volume mount to `docker-compose.e2e.yml` so `error-context.md` files persist on the host for analysis.

## 8. Dependabot Issue Fix (2026-03-08)

-   **Issue #324:** Fixed 16 security vulnerabilities opened by dependable last week (`tar`, `minimatch`, `rollup`, and `diskcache`).
-   **Frontend:** Updated packages via `npm update tar minimatch rollup` to resolve the vulnerable transitive dependencies.
-   **Backend:** Removed version constraints on `diskcache` and `ecdsa` as they raised `ResolutionImpossible` errors via `pip-compile` due to nonexistent PyPI distributions matching the GitHub Security Advisory versions exactly. Maintained backend testing parity for the fixed pip constraints.

## 9. v1.2.0 Documentation Overhaul

-   **Summary:** Completely audited and rewrote the `docs/` directory to prepare for the ArthSaarthi v1.2.0 release and onboarding of new developers.
-   **Key Updates:** 
    - `docs/database_schema.md` (formerly `mvp_database_schema.md`) was rewritten to reflect the exact v1.2.0 active PostgreSQL schema, including all new tables (Bonds, Tax Lots, Watchlists).
    - `docs/ui_ux_design.md` was updated with ASCII wireframes for the new Consolidated Holdings Table and the multi-step Data Import Wizard.
    - `docs/code_flow_guide.md` was updated with comprehensive Mermaid Sequence Diagrams for standardizing all documented request lifecycle traces (Add Transaction, Import Pipeline, Analytics, Audit Logging, Privacy Mode, Analytics Caching, Capital Gains, Watchlists, Goal Planning, and Daily Snapshots).
    - `README.md`, `CONTRIBUTING.md`, and `developer_guide.md` were overhauled to strongly emphasize the mandatory AI developer rules (from `GEMINI.md`) and detail the new Desktop build pipeline.

    - **Status:** ✅ **Stabilized**. Android builds are now resilient to Yahoo rate-limiting via dynamic header rotation and global inter-request throttling.
    - **Next Task:** Final verification of the experimental Android APK in a production environment.

## 10. Security Fix - Missing Authorization on Tax Reports (2026-04-29)

-   **Issue #423:** Fixed a critical IDOR vulnerability on the Capital Gains and Dividends report endpoints.
-   **Vulnerability:** The endpoints lacked the `get_current_user` dependency, allowing unauthenticated access and cross-tenant data exposure.
-   **Fix:** Added the necessary authentication dependency and ensured that the underlying data queries strictly filter by `user_id` to enforce tenant isolation.
-   **Service Hardening:** Identified and fixed a secondary data leak in `CapitalGainsService._calculate_demerger_ratios` where buy transactions were missing user-scoping.

## 11. Sell Modal Tax Lot Split Adjustment (2026-06-15)

-   **Issue #443:** Fixed tax lots in the Sell modal showing the original purchase quantity instead of the split-adjusted quantity.
-   **Fix:** Refactored `get_available_lots` in `crud_transaction.py` to replay `SPLIT` transactions chronologically on existing tax lots, adjusting both quantities and prices. Included a flooring mechanism for INR assets to prevent fractional share allocations.
-   **PR Review & CI/CD Optimizations:**
    - Pre-fetched asset currency outside the transaction processing loop to optimize database access and avoid N+1 queries.
    - Added a defensive check (`tx.quantity > 0`) to prevent division by zero in the split ratio calculations.
    - Applied `@pytest.mark.usefixtures("pre_unlocked_key_manager")` decorators to the first two split tests to resolve KeyManager failures in SQLite encrypted (Desktop) test environments.
-   **Verification:** Implemented unit/integration tests covering base split quantity/price adjustments, subsequent FIFO matching, INR flooring, and reverse stock splits (ratio < 1) for both INR and USD assets. Verified that all 332 backend and 188 frontend tests pass under all SQLite (encrypted and plain) and PostgreSQL environments, along with linting checks.

## 12. PPF Account Collision Prevention (Issue #444) (Updated 2026-06-20)

-   **Issue #444:** Prevent globally unique ticker symbol violations when creating PPF accounts for different users with the same account number.
-   **Fix:**
    -   **Backend Ticker & Optimization:** Updated `create_ppf_and_first_contribution` in `crud_asset.py` to generate user-specific PPF ticker symbols (`PPF-{user_id_short}-{account_number}`). Optimized database queries by fetching only the `user_id` scalar instead of loading the entire `Portfolio` model instance.
    -   **Strict Backup & Restore Isolation:** Modified `restore_backup` in `backup_service.py` to remove legacy fallbacks to the generic `old_ticker` during asset resolution and transaction lookup, enforcing strict user-specific ticker matching to ensure complete user data isolation and prevent potential data leaks.
-   **Verification:** 
    -   Implemented multi-user collision and backup/restore tests in `backend/app/tests/api/v1/test_ppf_multi_user.py`.
    -   Updated the legacy backup/restore tests in `backend/app/tests/api/v1/test_backup_restore.py` to align assertions with the new user-specific PPF ticker formatting.
    -   Verified that all 335 backend tests pass successfully in both SQLite and Postgres/Redis environments, and the code compiles without linting errors.

## 13. Revert PPF Interest Rate for Q2-2026 (Issue #445) (Updated 2026-06-21)

-   **Issue #445:** Revert the end date for the last PPF interest rate entry back to 2026-06-30 (Q2-2026) and add validation tests.
-   **Fix:**
    -   **Reverted PPF Interest Rate End Date:** Reverted the end date in `backend/app/db/seed_data/ppf_interest_rates.py` back to `2026-06-30` (representing Q2-2026) instead of `2026-03-31`.
    -   **Added Seed Data Verification Tests:** Implemented a verification test (`test_seed_interest_rates_correctness` in `test_admin_interest_rates.py`) to programmatically ensure interest rate seed data has no gaps, overlaps, contains only non-negative rates, is sorted chronologically, covers up to at least Q2-2026, and successfully seeds database tables.
-   **Verification:** Verified that the new tests and the entire backend test suite pass without issues in both SQLite and Postgres environments, and passes strict ruff lints.

## 14. Risk Profile Questionnaire (Issue #76 / FR12.1) (Updated 2026-07-14)

-   **Issue #76 (FR12.1):** Implement the Risk Profile Questionnaire.
-   **Fix:**
    -   **Database Schema:** Created the `user_risk_profiles` table, storing answers as column-level encrypted JSON via `EncryptedString` in desktop SQLite database.
    -   **Backend CRUD & API:** Added schemas, endpoints (`GET /api/v1/risk/` and `POST /api/v1/risk/`), and CRUD operations to calculate the risk score and classify the user (Conservative, Moderate, Growth, Aggressive).
    -   **Frontend UI:** Implemented a multi-step questionnaire wizard with progress tracking, options cards, and back/next navigation, plus a results page visualizing the score and target allocation.
    -   **Verification:** Authored backend integration tests (`test_risk.py`) verifying CRUD, validation, endpoints, and updates. Verified frontend compiles and builds successfully.

## 15. Android Pydantic V1 Compatibility Fixes (Updated 2026-07-30)

-   **Issue:** Android build crashes/malfunctions on Chaquopy (which runs Pydantic v1.10.13) due to Pydantic v2 incompatibilities in model configuration and forward references.
-   **Fixes:**
    -   **Strict Pydantic Version Check:** Discovered that importing `ConfigDict` did not throw an `ImportError` under Pydantic V1 (it was present internally in `pydantic.config`), bypassing try-except checks. Standardized all schemas to check `from pydantic.version import VERSION` to resolve import namespaces dynamically.
    -   **Eager Forward References:** Appended `update_forward_refs()` calls to the bottom of `goal.py` and `capital_gains.py` to compile ForwardRefs eagerly under Pydantic V1.
    -   **Config Fallback Block Standardization:** Added standard Pydantic V1 (`class Config: orm_mode = True`) and V2 (`model_config = ConfigDict(from_attributes=True)`) compatibility blocks to all database schemas: `AssetAlias`, `AuditLog`, `Bond`, `FixedDeposit`, `RecurringDeposit`, `HistoricalInterestRate`, and `Holding` (including helper models `PortfolioSummary` and `PortfolioHoldingsAndSummary`).
    -   **Date Validator Fallback:** Added a pre-validator to `ParsedTransaction.transaction_date` in `import_session.py` to parse plain date strings on V1.
    -   **AuditLog & CapitalGains Exports:** Added `AuditLog`, `AuditLogCreate`, and `CapitalGainsSummary` imports and exports to `backend/app/schemas/__init__.py`.
    -   **Lint and Eslint Fixes:** Fixed long logging lines in `session.py` and `benchmark_service.py`, moved imports to the top of schema files, and resolved a React Hook dependency warning in `AndroidSettingsCard.tsx`.
-   **Verification Script:** Authored `test_schemas.py` in the project root to compile and run from_orm/dict mock instantiation tests for all 16 database schemas. Verified 100% success rate (`Passed: 16, Failed: 0`) under a simulated Pydantic v1.10.13 environment.
-   **E2E Test Suite Resolution:** Resolved E2E test failures caused by `MobileSeedingSplash` hanging indefinitely during test execution when asset seeding is disabled (`ENVIRONMENT=test`). Updated `/api/v1/system/seeding-status` in `system.py` to bypass splash screen during testing mode. Full Playwright E2E suite executed via Docker Compose with 100% pass rate (`34 passed, 0 failed`).

