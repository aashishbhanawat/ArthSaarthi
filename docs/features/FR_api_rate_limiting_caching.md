
# Functional Requirement Specification: API Rate Limiting, Caching, and Request Batching (NFR13)

**Feature ID:** FR-NFR13-RateLimitCache  
**GitHub Issue:** [#559](https.github.com/aashishbhanawat/ArthSaarthi/issues/559)  
**Title:** Robust API Rate Limiting, Multi-Tier Caching, and Request Batching Layer  
**Target Release:** v1.5.0  

---

## 1. Sub-component Breakdown & Micro-Phases

### Phase 2.1: Multi-Tier Cache Layer (In-Memory + DiskCache / Redis)
* Implement L1 (In-Memory LRU cache) and L2 (DiskCache/Redis) cache facade in `app/core/cache.py`.
* Configurable TTLs per asset class: Real-time stock quotes (15 mins during market hours, 12 hours off-market), Mutual Fund NAVs (24 hours), FX Rates (6 hours).

### Phase 2.2: Rate Limiter & Token Bucket Engine
* Token bucket rate limiting engine for external providers (Zerodha: 3 req/sec; ICICI Breeze: 100 req/min; Upstox: 10 req/sec).
* Automatic sliding window tracking with Redis / DiskCache storage keys.

### Phase 2.3: Request Batching Engine
* Group single-symbol asset price requests into bulk multi-symbol requests (e.g. 50 tickers per Kite quote request).
* Transparent async request debouncer aggregating concurrent calls over a 50ms window.

### Core Data Security & Cache Policy
* **API Credentials Are Private to Each User:** API Keys, API Secrets, and OAuth Tokens are **strictly isolated per-user** and never shared across user accounts.
* **Price Cache Is Shared:** Market price values (e.g., `NSE:RELIANCE` LTP) fetched from public or authenticated sources are cached centrally (`Redis`/`DiskCache`), ensuring subsequent price lookups for any user are served instantly from cache without consuming extra API quota.

---

## 2. Technical Specification (Backend & Frontend)

### 2.1 Backend Implementation Details
* **Cache Manager (`backend/app/core/cache.py`):**
  * Support both Redis (`aioredis`) and `diskcache` seamlessly based on `REDIS_URL` setting.
  * Decorative `@cached_market_data(ttl=900)` utility.
* **Rate Limiter (`backend/app/services/rate_limiter.py`):**
  * Token bucket algorithm implementation.
  * Class `ProviderRateLimiter` raising `RateLimitExceededException` when bucket is empty.
* **Batch Processor (`backend/app/services/request_batcher.py`):**
  * `BatchQuoteFetcher`: Accepts symbol registration, accumulates for `batch_window_ms` (50ms) or `max_batch_size` (50 symbols), then fires bulk REST API call.

### 2.2 Frontend Implementation Details
* **Cache Health & Diagnostics Widget (`src/components/admin/CacheDiagnostics.tsx`):**
  * Admin view showing Cache Hit/Miss ratio, active rate limit status per provider, and button to purge cache manually.

---

## 3. Comprehensive Test Plan & Edge Cases

### 3.1 Edge Cases & Failure Scenarios
* **Rate Limit Exceeded:** When Zerodha 3 req/sec limit is hit, request batcher pauses requests for retry window (e.g., 333ms) or triggers immediate fallback to secondary provider (NSE Bhavcopy / Upstox).
* **Batch Split on Max Tickers:** Requesting 120 tickers with max batch size 50 splits into 3 parallel calls (50, 50, 20).
* **Market Hours Transition:** Dynamic TTL adjusting from 15 minutes during active trading session to 12 hours after market close to minimize unnecessary API calls.

### 3.2 Manual Testing Checklist
* [ ] Trigger portfolio valuation refresh for portfolio with 30+ holdings.
* [ ] Verify in server logs that individual symbol calls were batched into a single bulk provider call.
* [ ] Verify cache hits on subsequent page reloads without external HTTP requests.
* [ ] Test admin cache clear button in UI.

---

## 4. Automated Testing Strategy

### 4.1 Backend Pytest (`backend/app/tests/core/test_rate_limiting_caching.py`)
* Test token bucket refill rate under simulated rapid calls.
* Test cache expiration and dynamic TTL calculation.
* Test batching processor with async concurrency (`pytest-asyncio`).

### 4.2 Frontend Vitest (`src/components/admin/__tests__/CacheDiagnostics.test.tsx`)
* Test rendering cache diagnostic metrics and clear cache trigger.

### 4.3 E2E Playwright (`tests/cache-rate-limiting.spec.ts`)
* Test dashboard reload speed with warm vs cold cache.

---

## 5. UX & UI Specifications
* Admin Settings tab -> System Diagnostics section.
* Clear visual status bar for Provider API consumption (e.g., "Zerodha Kite: 42/1000 calls today (4.2%)").

---

## 6. Database Schema & Data Security

### 6.1 Database Schema
Optional table for persistence of usage metrics: `api_usage_logs`

```sql
CREATE TABLE api_usage_logs (
    id VARCHAR PRIMARY KEY,
    provider_name VARCHAR(50) NOT NULL,
    window_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    request_count INT DEFAULT 1,
    endpoint VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_api_usage_provider_time ON api_usage_logs(provider_name, window_timestamp);
```

### 6.2 Encryption Requirements
* No secret keys stored in `api_usage_logs`. Cache keys in Redis/DiskCache use hashed identifiers to prevent leaking user symbol lists in shared Redis instances.

---

## 7. Required Documentation Updates

* **README.md:** Add notes on caching layer configuration (`CACHE_TYPE=diskcache` vs `CACHE_TYPE=redis`).
* **docs/code_flow_guide.md:** Document `BatchQuoteFetcher` and `ProviderRateLimiter` design.
* **docs/workflow_history.md:** Add entry upon completion.
* **docs/debugging_guide.md:** Document how to clear DiskCache or Redis if stale market data is observed.
* **docs/project_handoff_summary.md:** Update caching infrastructure state.
* **docs/requirements.md:** Mark NFR13 as `✅ Implemented`.

---

## 8. External Data Sources & API Specifications
* Applies to all external market data providers (Zerodha, ICICI Breeze, AMFI, Upstox, Yahoo Finance).

---

## 9. File & API Endpoint Inventory

### Files to Create / Modify
* **Create:** `backend/app/core/cache.py`
* **Create:** `backend/app/services/rate_limiter.py`
* **Create:** `backend/app/services/request_batcher.py`
* **Create:** `backend/app/api/v1/endpoints/cache_diagnostics.py`
* **Create:** `frontend/src/components/admin/CacheDiagnostics.tsx`
* **Modify:** `backend/app/services/financial_data_service.py`

### API Routes
* `GET /api/v1/admin/cache/stats` - Fetch cache hit/miss statistics and rate limit consumption
* `POST /api/v1/admin/cache/clear` - Flush cache entries

---

## 10. Mobile-Friendly UI & Responsive Design
* Compact diagnostic card grid adapting to mobile screen widths.

---

## 11. Android Compatibility & Python Library Constraints
* **DiskCache Support:** Use `diskcache` library (pure Python with SQLite backend) for non-Redis / desktop / Android mobile environments. `diskcache` has zero C-extension dependencies and runs natively on Chaquopy / Android embedded Python.
