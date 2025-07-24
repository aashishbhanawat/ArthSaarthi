# Feature Plan: Real Data Integration

This document outlines the detailed development plan for replacing the mock financial data service with a real-time data provider.

**Related Requirements:** FR5

---er

## 1. Objective

To provide users with accurate, real-time market data for their assets. This involves refactoring the `FinancialDataService` to connect to a third-party financial data API, replacing the current hardcoded mock data.

---

## 2. Data Integration Strategy

We will adopt a two-part strategy for data integration to ensure a robust and user-friendly experience.

### 2.1. Asset Discovery & Database Seeding

*   **Source:** We will use the **ICICI Direct Security Master** file, a public CSV containing a comprehensive list of all securities on Indian exchanges.
*   **Implementation (NSE-First Priority):** A new backend script will be created to download and parse the master file. For each security (identified by its unique ISIN), the script will create a single entry in our local `assets` table, prioritizing the NSE ticker if the stock is dually-listed. This provides a definitive, local source of truth for all assets and simplifies the user experience.

### 2.2. Real-time Price Fetching

*   **Source:** We will use **Yahoo Finance** via the `yfinance` Python library to fetch the latest market prices.
*   **Implementation (Batching):** The `FinancialDataService` will be refactored to use `yfinance`. It will be optimized to fetch prices for **multiple tickers in a single batch request** using `yfinance.Tickers`, significantly improving performance and reducing the number of external API calls.

### 2.3. Caching & Refresh Strategy

*   **Caching Layer:** To improve performance and reduce external API calls, we will introduce a **Redis cache**. The `FinancialDataService` will cache the results of price lookups from `yfinance` with a short Time-To-Live (TTL, e.g., 15 minutes).
*   **Valuation & Refresh Mechanism:**
    *   By default, the dashboard will load quickly using the most recently available prices (either from the cache or the last known closing prices).
    *   The frontend will feature a **"Refresh" button**. Clicking this button will trigger a refetch of all dashboard data, providing the user with on-demand live prices.
    *   The UI will also display a "Last Updated" timestamp to provide context to the user.

---

## 3. Backend Development Plan

**Roles:** Backend Developer, Database Administrator

### 3.1. Configuration

*   **Environment Changes:** The `FINANCIAL_API_KEY` and `FINANCIAL_API_URL` variables will be removed from `backend/.env` and `app/core/config.py`.
*   **New Service (Docker):** A `redis` service will be added to the `docker-compose.yml` file.
*   **New Dependency (Backend):** The `redis` Python library will be added to `backend/requirements.txt`.

### 3.2. New Data Ingestion Script

*   A new script, `backend/app/scripts/seed_assets.py`, will be created to handle the download and parsing of the ICICI Security Master file and populate the `assets` table.

### 3.3. Service Layer Refactor (`financial_data_service.py`)

The `FinancialDataService` will be refactored to use the `yfinance` library and implement Redis caching. It will expose a new method, `get_multiple_asset_prices(tickers: List[str])`, to fetch data in a single batch. The `get_asset_details` method will be removed, as asset discovery is now handled by the local database and the seeding script.

*   **Error Handling:** The service will be updated with robust error handling to manage API failures, such as invalid tickers (404) or API key issues (401/403).

### 3.4. Other Layers

*   **Database Schema Change:** The `assets` table will be updated to include `exchange` (String) and `isin` (String, UNIQUE) columns. This is critical for the new strategy.
*   **API Endpoint Changes:** The `GET /api/v1/assets/lookup/{ticker}` endpoint will be refactored. It will now perform a search against our local `assets` table instead of making a live external API call.
*   **Frontend Impact:** The user experience for asset lookup will be significantly faster and more reliable. The dashboard will require UI changes to add a "Refresh" button and a "Last Updated" timestamp.

---