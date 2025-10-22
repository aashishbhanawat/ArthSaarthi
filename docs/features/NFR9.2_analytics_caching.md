# Feature Plan: Caching for Analytics Endpoints

**Status: ✅ Done**
**Feature ID:** NFR9.2
**Title:** Implement Caching for Analytics Endpoints
**User Story:** As a user, I want my portfolio analytics to load quickly, even for large portfolios with long transaction histories, so that I can get immediate insights into my performance.

---

## 1. Objective

To improve the performance and responsiveness of the application's main analytics endpoints by implementing a caching layer for the calculated results. This is a non-functional requirement that will reduce redundant CPU-intensive calculations for data that has not changed, leading to a faster user experience and reduced server load.

This feature will be built on top of the pluggable caching infrastructure established in **NFR9**.

---

## 2. High-Level Requirements

1.  **Cache Expensive Calculations:** The JSON results of the following expensive analytics endpoints must be cached:
    *   `/api/v1/portfolios/{id}/summary`
    *   `/api/v1/portfolios/{id}/analytics`
    *   `/api/v1/portfolios/{portfolio_id}/assets/{asset_id}/analytics`
    *   `/api/v1/dashboard/summary`

2.  **Cache TTL:** All cached analytics data should have a Time-To-Live (TTL) of 15 minutes. This provides a good balance between performance and data freshness.

3.  **Cache Invalidation:** A robust cache invalidation mechanism must be implemented. The cache for a specific portfolio must be cleared immediately whenever a transaction is created, updated, or deleted for that portfolio. This ensures data consistency.

---

## 3. Technical Design

1.  **Cache Decorator:**
    *   A new decorator, e.g., `@cache_analytics_result`, will be created. This decorator will be applied to the main CRUD functions that power the analytics endpoints (e.g., `crud_holding.get_portfolio_holdings_and_summary`, `crud_analytics.get_portfolio_analytics`).
    *   The decorator will generate a unique cache key based on the function arguments (e.g., `analytics:portfolio:{portfolio_id}`).
    *   It will first check the cache for the key. If found, it returns the cached result. If not, it will execute the function, store the result in the cache with a 15-minute TTL, and then return the result.

2.  **Cache Invalidation Logic:**
    *   A cache invalidation function, e.g., `invalidate_portfolio_cache(portfolio_id: UUID)`, will be created.
    *   This function will be called from the transaction management endpoints (`/api/v1/transactions/` and `/api/v1/import-sessions/{id}/commit`) after any successful `POST`, `PUT`, or `DELETE` operation that modifies a portfolio's data.
    *   It will delete all relevant cache keys associated with that `portfolio_id`.

---

## 4. Implementation Plan

1.  Create the `@cache_analytics_result` decorator.
2.  Apply the decorator to the relevant CRUD functions in `crud_holding.py` and `crud_analytics.py`.
3.  Create the `invalidate_portfolio_cache` function.
4.  Integrate the invalidation function into all relevant API endpoints that modify transaction data.
5.  Add unit tests to verify that a cached result is returned on the second call and that the cache is correctly invalidated after a transaction is modified.