# Project Handoff & Status Summary

**Last Updated:** 2026-04-16

## 1. Current Project Status

*   **Overall Status:** ✅ **Stable (v1.2.0 Released)** | 📱 **Android Native App Stabilized (Experimental)**
*   **Summary:** Successfully consolidated Android build workflows into the main release and test pipelines. Aligned the backend test suite for `android` deployment mode, ensuring full functional parity and stability. Formalized Android-specific requirements (FR14.4, NFR14) and documented critical native settings for battery optimization, permissions, and background execution.

## 2. Test Suite Status

*   **Backend Unit/Integration Tests (Postgres/Redis):** ✅ **310/310 Passing**
*   **Backend Integration Tests (Android/SQLite):** ✅ **304/310 Passing** (6 expected skips for admin-only APIs)
*   **Frontend TypeScript Compilation:** ✅ **Zero Errors**
*   **Linters (Code Quality):** ✅ **Passing (0 Errors)**

### Recent Stabilization & Refinement Efforts

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
-   **Automated Data Import:** Support for Zerodha, ICICI Direct (Tradebook & Portfolio), MFCentral CAS, CAMS, KFintech, Zerodha Coin, and generic CSV files. Also includes **Fixed Deposit (FD) PDF imports** (HDFC, ICICI, SBI) with password protection support. Supports **asset alias mapping** with admin management (view, edit, delete) of all aliases.
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
-   **Cache Invalidation:** `invalidate_caches_for_portfolio` deletes all range-specific dashboard history keys, portfolio analytics, holdings, and stale `DailyPortfolioSnapshot` DB records. Restore does comprehensive cache flush across all user data.

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
