# PR Description

## feat(analytics): Fix Portfolio FD Analytics, Backend Health Check, and Desktop Stability (#330, #332, #333, #334)

### Summary
This PR addresses several critical issues identified in version 4.0:
1. **Benchmark Simulation for Debt-only Portfolios**: Fixed a bug where FD/RD-only portfolios showed 0% XIRR by implementing synthetic transactions for benchmark simulations.
2. **XIRR UX Improvements**: Added "(Annualized)" labels to Benchmark Comparison for periods < 1 year and standardized percentage scaling.
3. **Backend Reliability**: Increased health check `start_period` for long-running startup seeding and added default `SECRET_KEY` for MacOS stability.
4. **Data Integrity**: Implemented timezone-aware future date validation and duplicate FD detection.
5. **Build Resolution**: Fixed `bcrypt` dependency conflict on Windows.

### Changes
*   **feat(backend)**: Implemented `_generate_synthetic_transactions` in `BenchmarkService`.
*   **feat(backend)**: Added `days_duration` to benchmark response and fixed maturity inflow logic in `_get_portfolio_cash_flows`.
*   **feat(backend)**: Added duplicate FD check in `crud_fixed_deposit`.
*   **feat(backend)**: Implemented timezone-aware `model_validator` in `TransactionBase` and `FixedDepositBase`.
*   **fix(backend)**: Added default `SECRET_KEY` using `secrets.token_urlsafe(32)`.
*   **fix(build)**: Increased Docker health check `start_period` to 1200s and updated `bcrypt` to 4.1.3.
*   **feat(frontend)**: Updated `BenchmarkComparison.tsx` with "(Annualized)" labels and standardized formatting.
*   **feat(frontend)**: Updated `TransactionFormModal.tsx` and FD forms with `max` date constraints to prevent future date logging.
*   **feat(frontend)**: Updated `portfolioApi.ts` types to support `days_duration`.

### Verification
*   **Manual Verification**: Confirmed FD-only portfolios show correct XIRR in Benchmark Comparison.
*   **Validation Testing**: Verified future date and duplicate FD rejection via UI and unit tests.
*   **Build Verification**: Confirmed successful backend startup on initial seeding.
*   **Test Suite**: 298/298 backend tests passing.

### Related Issues
*   Fixes #330 (Backend Startup Timeout)
*   Fixes #332 (FD Analytics, Future Date Validation, Duplicate FDs)
*   Fixes #333 (MacOS Desktop Crash)
*   Fixes #334 (Windows Build bcrypt conflict)
