## 2025-07-22 - Fix IDOR/Data Leakage in PPF Holdings Calculation
**Vulnerability:** The `process_ppf_holding` function aggregated all transactions globally for a shared asset when `portfolio_id` was `None` because it failed to filter by the requesting `user_id`.
**Learning:** Shared global entities like `Asset` require strict tenant isolation queries when retrieving linked context models. Global utility methods frequently lack implicit authorization context.
**Prevention:** Always verify that `get_multi_by_*` methods include a `user_id` or join through a user-owned entity (like `Portfolio`) to guarantee tenant separation, even in aggregation scopes.

## 2024-05-18 - Fix Information Leakage in Error Responses
**Vulnerability:** Several endpoints were catching generic exceptions and returning `str(e)` directly in the HTTP response JSON (e.g., `detail=f"Error: {str(e)}"`), which could leak sensitive internal database details or stack traces to malicious actors.
**Learning:** Returning raw exception strings directly to the client violates secure coding practices because it exposes internal implementation details.
**Prevention:** Catch exceptions, log them internally using `logger.error(..., exc_info=True)` to retain context for debugging, and return safe, generic error messages to the client.
