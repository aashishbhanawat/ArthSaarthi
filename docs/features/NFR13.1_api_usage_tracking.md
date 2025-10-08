# Non-Functional Requirement: API Usage Tracking & Rate Limiting

**Status: 📝 Planned**
**Feature ID:** NFR13.1
**Title:** Implement API Usage Tracking and Rate Limiting

---

## 1. Objective

To ensure the application is a good citizen, manage costs for paid APIs, and enable robust fallback logic, a usage tracking and rate-limiting mechanism will be built into the provider architecture.

The primary goals are:
*   Prevent hitting hard rate limits imposed by external API providers (e.g., 100 calls/minute).
*   Allow users to set their own, stricter limits for cost management on paid APIs.
*   Enable the `FinancialDataService` to fall back to a secondary provider if the primary provider's self-imposed limit is reached.

---

## 2. High-Level Design

1.  **Usage Tracking:** The application's cache (`Redis` or `DiskCache`) will be used to store API call counts for each provider. Keys will be structured to track usage over different time windows (e.g., `usage:provider_name:minute`, `usage:provider_name:day`).
2.  **Configurable Limits:**
    *   **System Defaults:** Default rate limits for each provider will be defined in the application's configuration.
    *   **User Overrides:** A new database table and API will be created to allow users to set their own, stricter limits for each provider. This is especially important for APIs where the user provides their own key.
3.  **Enforcement:**
    *   Before a provider makes an external API call, it will check its current usage against the configured limits.
    *   If a limit is exceeded, the provider will raise a custom `RateLimitExceededError`.
4.  **Fallback Logic:** The main `FinancialDataService` will wrap calls to its providers in a `try...except` block. If it catches a `RateLimitExceededError`, it will log the event and attempt to use the next provider in its fallback chain.

---

## 3. Example Workflow

1.  A user wants to fetch the price of "TCS.NS".
2.  The `FinancialDataService` decides to use the `ZerodhaKiteProvider`.
3.  The `ZerodhaKiteProvider` checks the user's configured limits (e.g., 50 calls/minute).
4.  It queries the cache for the key `usage:zerodha:minute`. The count is 49.
5.  The limit is not exceeded. The provider makes the API call to Kite Connect.
6.  On a successful response, it increments the `usage:zerodha:minute` and `usage:zerodha:day` counters in the cache.
7.  Later, another request comes in. The `usage:zerodha:minute` count is now 50.
8.  The `ZerodhaKiteProvider` sees the limit is reached and raises `RateLimitExceededError` without making an API call.
9.  The `FinancialDataService` catches the error and falls back to using the `NseBhavcopyProvider` to fulfill the request.
