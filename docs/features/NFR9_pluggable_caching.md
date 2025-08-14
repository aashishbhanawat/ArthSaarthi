# Feature Plan: Pluggable Caching Layer (NFR9)

## 1. Objective

To replace the hard dependency on Redis with a pluggable caching layer. This is a critical non-functional requirement (NFR) that will allow the application to use a simple, in-process, in-memory cache for non-Docker and single-executable deployments. This removes the operational overhead of requiring a separate Redis server for simpler installation scenarios.

## 2. Functional Requirements

*   **NFR9: Pluggable Caching:** The application must support both Redis (for production/Docker) and a lightweight in-memory cache (for single-file/simple deployments).

## 3. High-Level Technical Design

The implementation will follow the **Strategy Pattern**, abstracting the caching logic behind a common interface.

*   **Configuration:**
    *   A new environment variable, `CACHE_TYPE`, will be introduced. It will accept `redis` (default) or `in-memory`.
    *   The `app/core/config.py` settings will be updated to manage this.

*   **Cache Abstraction Layer:**
    *   A new `app/cache` module will be created.
    *   An abstract base class, `CacheClient`, will define the common interface for all caching operations (e.g., `get_json`, `set_json`, `delete`).

*   **Concrete Implementations:**
    *   `RedisCacheClient`: A class that implements the `CacheClient` interface using the `redis-py` library. This will be the default.
    *   `DiskCacheClient`: A new class that implements the `CacheClient` interface using the `diskcache` library.

*   **Rationale for `diskcache` over `cachetools`:**
    *   **Resource Management:** The primary concern for a non-Docker/executable deployment is resource consumption on the user's machine. A pure in-memory cache like `cachetools` has an unbounded memory footprint, which could cause significant issues on devices with limited RAM, especially when caching large historical datasets.
    *   **Low Memory Footprint:** `diskcache` addresses this directly by storing cached items on the file system, keeping the application's RAM usage minimal and predictable.
    *   **Acceptable Trade-offs:** While `diskcache` introduces file I/O (making it slightly slower than an in-memory cache) and creates a cache directory on the user's system, these are acceptable trade-offs for the significant benefit of memory stability. The cache directory will be placed in a standard user data location (e.g., using `platformdirs`).
    *   **Feature Parity:** `diskcache` supports per-item TTL (`expire`), which is a feature of Redis that `cachetools.TTLCache` does not, making it a more feature-complete alternative.

*   **Cache Factory:**
    *   A factory function, `get_cache_client()`, will be created. It will read the `CACHE_TYPE` from the settings and return a singleton instance of the appropriate cache client.

*   **Dependency Injection:**
    *   The `FinancialDataService`, which is the primary consumer of the cache, will be refactored. Instead of creating its own Redis client, it will accept a `CacheClient` instance in its constructor.
    *   The service will be initialized at startup with the correct cache client provided by the factory.

### 3.1. Deployment & Testing

*   **Docker (Default):** The standard `docker-compose.yml` will continue to use the `redis` service, and the backend will default to `CACHE_TYPE=redis`.
*   **Docker (SQLite):** The `docker-compose.sqlite.yml` override will be updated to set `CACHE_TYPE=disk` for the backend service and will no longer depend on the `redis` service.
*   **Testing:** The test environments (`docker-compose.test.yml`, `docker-compose.e2e.yml`) will be configured to use the `disk` cache. This simplifies the test setup and removes a dependency, making the CI/CD pipeline more robust.

## 4. Implementation Plan

1.  Add `diskcache` to `backend/requirements.txt`.
2.  Update `app/core/config.py` to include the `CACHE_TYPE` setting (accepting `disk` instead of `in-memory`).
3.  Create the `app/cache` module with the `CacheClient` interface and the `RedisCacheClient` and `DiskCacheClient` implementations.
4.  Implement the `get_cache_client()` factory.
5.  Refactor `FinancialDataService` to use the injected `CacheClient`.
6.  Update `docker-compose.sqlite.yml`, `docker-compose.test.yml`, and `docker-compose.e2e.yml` to use the disk-based cache.
7.  Update all relevant documentation (`README.md`, `project_handoff_summary.md`, etc.).

---

This plan provides a clean, maintainable, and decoupled architecture for caching, significantly improving the application's portability.
