# Feature Plan: Dashboard Visualization with Charts

This document outlines the detailed development plan for enhancing the dashboard with data visualization charts.

**Related Requirements:** FR5 (Dashboard), Next Steps from Handoff

---

## 1. Objective

To provide users with a visual representation of their portfolio's performance over time and its current asset allocation. This will be achieved by adding two new chart components to the dashboard: a historical performance line chart and an asset allocation pie chart.

---

## 2. Backend Development Plan

**Roles:** Backend Developer, Database Administrator

### 2.1. API Enhancements

The current `/api/v1/dashboard/summary` endpoint is insufficient for charting. We will create two new, dedicated endpoints for this purpose.

*   **New Endpoint 1: Portfolio History**
    *   **Route:** `GET /api/v1/dashboard/history`
    *   **Query Parameters:** `range` (string, e.g., "7d", "30d", "1y", "all")
    *   **Description:** Returns time-series data of the user's total portfolio value.
    *   **Success Response (200 OK):**
        ```json
        {
          "history": [
            { "date": "2025-07-15", "value": 10000.50 },
            { "date": "2025-07-16", "value": 10150.75 },
            { "date": "2025-07-17", "value": 10120.00 }
          ]
        }
        ```

*   **New Endpoint 2: Asset Allocation**
    *   **Route:** `GET /api/v1/dashboard/allocation`
    *   **Description:** Returns the current market value of each asset held by the user, grouped by ticker symbol.
    *   **Success Response (200 OK):**
        ```json
        {
          "allocation": [
            { "ticker": "AAPL", "value": 5200.00 },
            { "ticker": "GOOGL", "value": 3100.50 },
            { "ticker": "BTC", "value": 1700.25 }
          ]
        }
        ```

### 2.2. Backend Logic (`crud_dashboard.py`)

*   New functions will be added to `app/crud/crud_dashboard.py` to perform the necessary calculations by querying the `transactions` table.
*   The logic will need to calculate daily portfolio snapshots for the history endpoint and aggregate current holdings for the allocation endpoint.

### 2.3. Database Schema

*   No database schema changes are required. All data can be derived from existing tables.

---

## 3. Frontend Development Plan

**Roles:** Frontend Developer, UI/UX Designer

### 3.1. API Integration & State Management

*   **New Hooks (`frontend/src/hooks/useDashboard.ts`):**
    *   `useDashboardHistory(range)`: A new React Query hook to call the `/api/v1/dashboard/history` endpoint. It will be re-fetched when the `range` parameter changes.
    *   `useDashboardAllocation()`: A new React Query hook to call the `/api/v1/dashboard/allocation` endpoint.

### 3.2. New UI Components

*   **`frontend/src/components/Dashboard/PortfolioHistoryChart.tsx`:**
    *   Will contain the line chart for portfolio performance.
    *   Will include a button group to allow the user to select the time range ("7D", "30D", "1M", "1Y", "All"), which will update the `range` state passed to the `useDashboardHistory` hook.
*   **`frontend/src/components/Dashboard/AssetAllocationChart.tsx`:**
    *   Will contain a pie or doughnut chart to visualize the portfolio's composition by asset.

### 3.3. Component Updates

*   **`frontend/src/pages/DashboardPage.tsx`:**
    *   Will be updated to include the two new chart components, placing them in a logical layout alongside the existing `SummaryCard` and `TopMoversTable`.

---

## 4. Testing Plan

**Role:** QA Engineer

*   **Backend:**
    *   Write unit tests for the new `crud_dashboard` calculation logic.
    *   Write integration tests for the new `/dashboard/history` and `/dashboard/allocation` API endpoints, verifying correct responses for different users and time ranges.
*   **Frontend:**
    *   Write unit tests for the new `PortfolioHistoryChart` and `AssetAllocationChart` components. The tests will mock the `react-chartjs-2` library and the data hooks to ensure the components pass the correct data and configuration props to the charts.
    *   Test user interactions, such as clicking the time-range buttons in the history chart.