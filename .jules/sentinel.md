## 2025-07-22 - Fix IDOR/Data Leakage in PPF Holdings Calculation
**Vulnerability:** The `process_ppf_holding` function aggregated all transactions globally for a shared asset when `portfolio_id` was `None` because it failed to filter by the requesting `user_id`.
**Learning:** Shared global entities like `Asset` require strict tenant isolation queries when retrieving linked context models. Global utility methods frequently lack implicit authorization context.
**Prevention:** Always verify that `get_multi_by_*` methods include a `user_id` or join through a user-owned entity (like `Portfolio`) to guarantee tenant separation, even in aggregation scopes.
