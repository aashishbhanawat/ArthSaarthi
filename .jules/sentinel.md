## 2026-04-29 - Prevent information leakage in log retrieval
**Vulnerability:** The `get_logs` system endpoint leaked internal system information by returning the exact exception string (`str(e)`) to the client if log file reading failed.
**Learning:** In Python, catching a generic `Exception` and stringifying it can inadvertently expose sensitive file paths or environment constraints to unauthorized clients.
**Prevention:** API responses should always return safe, generic error messages (e.g., 'Error reading log file. Please check server logs.'), while the actual error details must be securely logged internally using `logger.error(..., exc_info=True)`.
## 2024-04-27 - [Missing Authorization on Tax Report Endpoints]
**Vulnerability:** [Missing authentication and authorization (IDOR) on Capital Gains and Dividends report endpoints allowed unauthenticated access and cross-tenant data exposure.]
**Learning:** [Endpoints created for tax reporting were not protected by the `get_current_user` dependency, bypassing identity verification and ownership checks.]
**Prevention:** [Always enforce authorization checks (`Depends(deps.get_current_user)`) on all non-public API endpoints and ensure queries are scoped by `user_id`.]
