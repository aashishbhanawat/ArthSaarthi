## 2024-04-27 - [Missing Authorization on Tax Report Endpoints]
**Vulnerability:** [Missing authentication and authorization (IDOR) on Capital Gains and Dividends report endpoints allowed unauthenticated access and cross-tenant data exposure.]
**Learning:** [Endpoints created for tax reporting were not protected by the `get_current_user` dependency, bypassing identity verification and ownership checks.]
**Prevention:** [Always enforce authorization checks (`Depends(deps.get_current_user)`) on all non-public API endpoints and ensure queries are scoped by `user_id`.]
## 2026-05-11 - Fix Missing Authorization (IDOR) on Goal Links
**Vulnerability:** In `create_goal_link`, users could provide any `portfolio_id` and link it to their own goal without verification of ownership. In `get_goal_with_analytics`, progress calculation for goals linked by `asset_id` fetched the first global transaction for that asset, leaking other users' portfolio values.
**Learning:** Shared entity references (like `portfolio_id` or `asset_id`) passed by users or used in aggregate queries must be strictly validated against the current user's scope.
**Prevention:** Always fetch the target resource (e.g., Portfolio) and assert `resource.user_id == current_user.id` before associating it. Always append `.filter(Model.user_id == current_user.id)` when querying cross-tenant tables like `transactions`.
