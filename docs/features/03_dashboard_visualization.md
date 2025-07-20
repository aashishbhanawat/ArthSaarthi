# Feature Plan: Dashboard Data Visualization

**Date:** 2025-07-19

## 1. Objective

To replace the static placeholder content on the dashboard with dynamic, meaningful data visualizations. This involves creating a backend endpoint to calculate and serve aggregated financial data and then using that data to render charts on the frontend.

---

## 2. Backend Plan

**Roles:** Backend Developer, Database Administrator

### 2.1. New API Endpoint

A new, read-only endpoint will be created to serve all the data required for the dashboard in a single request.

*   **Endpoint:** `GET /api/v1/dashboard/summary`
*   **Description:** Returns a calculated summary of the current user's financial holdings across all their portfolios.
*   **Authentication:** Requires a valid JWT for an authenticated user.

### 2.2. Request / Response Schemas

New Pydantic schemas will be created in `app/schemas/dashboard.py`.

*   **`DashboardAssetAllocation`**:
    *   `asset_type: str` (e.g., "Stock", "Crypto")
    *   `value: float`
*   **`DashboardPortfolioValue`**:
    *   `portfolio_name: str`
    *   `value: float`
*   **`DashboardSummary` (Response Body)**:
    *   `total_value: float`
    *   `asset_allocation: list[DashboardAssetAllocation]`
    *   `portfolio_values: list[DashboardPortfolioValue]`

### 2.3. Backend Logic Overview

The logic will reside in a new CRUD module (`app/crud/crud_dashboard.py`) to keep concerns separated.

1.  The endpoint will retrieve the current authenticated user.
2.  It will fetch all portfolios and their associated transactions for that user.
3.  It will iterate through every transaction, calculating the current market value of each holding.
    *   This requires fetching the current price for each asset's ticker symbol using the existing `FinancialDataService`.
    *   The value of a holding is `quantity * current_price`.
4.  The values will be aggregated to calculate:
    *   The total value for each individual portfolio.
    *   The total value across all portfolios.
    *   The total value for each asset type (e.g., sum of all "Stock" holdings).
5.  The aggregated data will be formatted using the `DashboardSummary` schema and returned.

### 2.4. Proposed File Changes

*   **Create:** `app/api/v1/endpoints/dashboard.py` (to define the new router and endpoint)
*   **Create:** `app/schemas/dashboard.py` (for the new Pydantic schemas)
*   **Create:** `app/crud/crud_dashboard.py` (to house the calculation logic)
*   **Update:** `app/api/v1/api.py` (to include the new dashboard router)
*   **Update:** `app/schemas/__init__.py` (to expose the new dashboard schemas)
*   **Update:** `app/crud/__init__.py` (to expose the new dashboard CRUD module)

## 3. Database Plan

**No database schema changes are required.** All necessary data can be calculated on-the-fly from the existing `portfolios`, `transactions`, and `assets` tables.

---

## 4. Frontend Plan (TBD)

The frontend will be planned in the next step. It will involve:
*   Creating a new React Query hook (`useDashboardSummary`) to fetch data from the new endpoint.
*   Integrating a charting library (e.g., Chart.js with `react-chartjs-2` or Recharts).
*   Replacing the placeholder components in `DashboardPage.tsx` with the new data-driven charts.

