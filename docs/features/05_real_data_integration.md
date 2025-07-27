# Feature: Real Data Integration

This document describes the implementation of the real-time financial data integration feature.

**Related Requirements:** FR5

---

## 1. Objective

To provide users with accurate market data for their assets by replacing the mock financial data service with a live one.

---

## 2. Implementation Strategy

The implementation uses a two-part strategy to ensure a robust and performant user experience.

### 2.1. Asset Discovery & Local Database

*   **Asset Seeding:** The application includes a command-line script (`backend/app/cli.py`) to seed the local `assets` table with a master list of securities.
*   **Asset Search:** The `GET /api/v1/assets/lookup/` endpoint searches *only* the local `assets` table. This makes searching for already-known assets extremely fast.
*   **New Asset Creation:** To add an asset not in the local DB, the frontend uses the `POST /api/v1/assets/` endpoint. This endpoint validates the ticker against `yfinance` and, if successful, creates the new asset in the local database before returning it. This two-step process (search local, then create if needed) ensures data integrity and a good user experience.

### 2.2. Real-time Price Fetching

*   **Source:** We will use **Yahoo Finance** via the `yfinance` Python library to fetch the latest market prices.
*   **Implementation (Batching):** The `FinancialDataService` is optimized to fetch prices for **multiple tickers in a single batch request**.
    *   `get_current_prices` uses `yfinance.Tickers` for efficient current price lookups.
    *   `get_historical_prices` uses `yfinance.download` for efficient historical data lookups.
    This batching strategy is critical for performance, especially on the main dashboard.

### 2.3. Caching & Refresh Strategy

*   **Caching Layer:** A **Redis cache** is implemented in the `FinancialDataService` to dramatically improve performance and reduce the number of external API calls.
    *   Current prices are cached with a short Time-To-Live (TTL) of 15 minutes.
    *   Historical data is cached with a longer TTL of 24 hours.

---

## 3. Backend Development Plan

### 3.1. Configuration & Dependencies

*   **Environment Changes:** The obsolete `FINANCIAL_API_KEY` and `FINANCIAL_API_URL` variables were removed from `backend/.env` and `app/core/config.py`.
*   **New Service (Docker):** A `redis` service was added to the `docker-compose.yml` file.
*   **New Dependencies (Backend):** The `redis` and `yfinance` Python libraries were added to `backend/requirements.txt`.

### 3.3. Service Layer Refactor (`financial_data_service.py`)

The `FinancialDataService` was refactored to use the `yfinance` library and implement Redis caching. The old mock methods (`get_asset_price`, `get_asset_details`) were removed. The service now correctly handles exchange suffixes (e.g., `.NS` for NSE) for `yfinance`.