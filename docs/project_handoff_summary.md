# Project Handoff & Status Summary

**Last Updated:** 2026-03-14

## 1. Current Project Status

*   **Overall Status:** 🟢 **Stable**
*   **Summary:** Fixed 6 dashboard/portfolio issues: cache invalidation for range-specific history keys, benchmark invested amount going negative after FD maturity, matured FDs/RDs appearing in portfolio history, incomplete cache invalidation on restore, PPF log spam, and added timing instrumentation. Previously implemented Dividend Report (FR 6.6) with Quarterly Advance Tax Buckets.

## 2. Test Suite Status

*   **Backend Unit/Integration Tests:** ✅ **300/300 Passing** (Includes Dividend API tests)
*   **Frontend TypeScript Compilation:** ✅ **Zero Errors**
*   **Linters (Code Quality):** ✅ **Passing**

### Recent Stabilization Efforts

*   **Advanced Benchmarking (FR6.3):** Implemented hybrid benchmarks (35/65, 50/50 equity/debt blends), risk-free rate overlay, and category-level (equity vs debt) XIRR comparison. Fixed XIRR calculation for category subsets to use actual current market value.
*   **Portfolio Delete Error Handling:** Catching FK constraint violations when deleting a portfolio linked to goals — returns a 409 Conflict with a user-friendly message instead of a 500. Frontend now displays this error via alert.
*   **Non-Market Asset Historical Chart:** Fixed multiple bugs where FDs, RDs, PPF, and Bonds showed `0` value on historical dates:
    *   Added `BOND` to `supported_types` for historical price fetching.
    *   Fixed PPF `process_ppf_holding` to support historical simulation without DB side-effects.
    *   Fixed early-return bug where FD/RD-only portfolios returned empty history.
    *   Fixed `Holding` schema crash for FDs/RDs missing an `account_number`.
*   **UI "No Data" Fix:** Category comparison no longer hides the entire component when a category has no transactions — keeps navigation elements visible.
*   **Desktop App Migration Fix:** Added `fmv_2018` to the manual schema migration script in `run_cli.py` to prevent startup crashes when upgrading the desktop app version.

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
-   **Capital Gains & Dividend Reporting:**
    -   Comprehensive Capital Gains reports for Schedule 112A (Grandfathered Equity) and Schedule FA (Foreign Assets).
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

## 9. Security Fix - Missing Authorization on Tax Reports (2026-04-29)

-   **Issue #423:** Fixed a critical IDOR vulnerability on the Capital Gains and Dividends report endpoints.
-   **Vulnerability:** The endpoints lacked the `get_current_user` dependency, allowing unauthenticated access and cross-tenant data exposure.
-   **Fix:** Added the necessary authentication dependency and ensured that the underlying data queries strictly filter by `user_id` to enforce tenant isolation.
