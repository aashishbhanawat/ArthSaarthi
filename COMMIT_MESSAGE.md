feat(analytics): Fix FD Benchmark XIRR, Annualization Labels, and Date Validation (#330, #332, #333, #334)

This PR resolves multiple issues related to portfolio analytics, backend stability, and data validation:

1. **Benchmark XIRR for FD-only Portfolios (#332)**:
   - Implemented synthetic transactions (BUY, DIVIDEND, SELL) for Fixed/Recurring Deposits to drive benchmark simulations.
   - Fixed maturity value inflows in portfolio cash flows to ensure correct terminal wealth calculation for matured FDs.
   - Standardized XIRR display scaling using a shared `formatPercentage` utility.

2. **XIRR Annualization Labels (#332)**:
   - Added "(Annualized)" labels to XIRR values in the Benchmark Comparison widget for periods shorter than one year to clarify returns.
   - Backend now calculates and returns `days_duration` to facilitate this labeling.

3. **Data Validation & Integrity (#332)**:
   - Implemented timezone-aware future date validation for Transactions and FDs.
   - Added duplicate detection for Fixed Deposits.
   - Enforced max date constraints on frontend date pickers.

4. **Reliability & Build Fixes (#330, #333, #334)**:
   - Increased Docker health check `start_period` (1200s) to accommodate long-running asset seeding.
   - Added default `SECRET_KEY` in `config.py` to prevent MacOS desktop crashes.
   - Updated `bcrypt` to 4.1.3 to resolve Windows build dependency conflicts.

5. **Misc**:
   - Added PPF Interest Rate for Apr-Jun 2026.
   - Adjusted FD maturity counting logic to prevent double-counting of matured instruments in analytics.
