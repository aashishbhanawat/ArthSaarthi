## 2025-02-28 - Cross-Tenant Data Leakage in Bond Ownership Check
**Vulnerability:** The `_check_bond_ownership` function in `backend/app/api/v1/endpoints/bonds.py` previously verified ownership by iterating through `bond.asset.transactions` and manually checking if the `portfolio.user_id` matched the current user. This exposed an N+1 query issue and, more importantly, could potentially leak data or raise errors if transaction data was shared improperly. It didn't correctly isolate the check to only the user's specific context.
**Learning:** Checking ownership of globally shared entities (like `Asset` via `asset_id`) requires robust, direct database queries that scope by the current user's ID to prevent IDOR and inefficient data access.
**Prevention:** Always verify ownership of shared assets by constructing a direct query joining the `Transaction` and `Portfolio` tables, filtering strictly by the authenticated `user_id`. Do not rely on iterating through ORM relationships (like `asset.transactions`).

## 2025-03-09 - Information Exposure via Unhandled Exceptions
**Vulnerability:** The `get_unrealized_capital_gains` endpoint in `backend/app/api/v1/endpoints/capital_gains.py` leaked internal error details to the client in HTTP 500 responses by including the raw exception string `str(exc)`.
**Learning:** Returning `str(exc)` in production environments exposes stack trace fragments or implementation details, potentially aiding an attacker in understanding backend logic or discovering further vulnerabilities.
**Prevention:** Catch-all exception handlers must return generic, sanitized error messages (e.g., "Internal server error") to the client. The full exception details, including stack traces (`exc_info=True`), should be strictly confined to internal server logs using `logger.error()`.
## 2025-02-27 - [Fix IDOR in Asset Transaction Fetching]
**Vulnerability:** Found an Insecure Direct Object Reference (IDOR) and cross-tenant data leakage risk in `crud_transaction.py` where `get_multi_by_asset` fetched all transactions for an asset globally without scoping by `user_id`.
**Learning:** Shared assets (like global bonds or equities) can have transactions spanning multiple tenants. Fetching globally and relying on Python-level filtering introduces both performance bottlenecks (O(N) overhead) and significant data leakage risks if filtering is overlooked.
**Prevention:** Always push tenant filtering to the database level by joining the `Portfolio` table and asserting `Portfolio.user_id == user_id` when aggregating or fetching shared asset transactions.
