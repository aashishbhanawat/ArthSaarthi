## 2024-04-27 - [Missing Authorization on Tax Report Endpoints]
**Vulnerability:** [Missing authentication and authorization (IDOR) on Capital Gains and Dividends report endpoints allowed unauthenticated access and cross-tenant data exposure.]
**Learning:** [Endpoints created for tax reporting were not protected by the `get_current_user` dependency, bypassing identity verification and ownership checks.]
**Prevention:** [Always enforce authorization checks (`Depends(deps.get_current_user)`) on all non-public API endpoints and ensure queries are scoped by `user_id`.]
