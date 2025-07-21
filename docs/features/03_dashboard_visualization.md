# Feature Plan: Dashboard Visualization

This document outlines the development plan for the frontend of the Dashboard Visualization feature.

**Related Requirements:** FR5 (Dashboard)

## 1. Frontend Development Plan

This plan was created by the **Frontend Developer** and **UI/UX Designer**.

### 1.1. Objective

To refactor the `DashboardPage` to consume the live `GET /api/v1/dashboard/summary` endpoint and display the key metrics in a series of clean, readable cards and tables.

### 1.2. Technology & Dependencies

*   We will install `chart.js` and `react-chartjs-2` to be prepared for future charting enhancements.

### 1.3. API Integration & State Management (React Query)

*   A new file, `frontend/src/hooks/useDashboard.ts`, will be created.
*   **New Hook:** `useDashboardSummary()` will call the `GET /api/v1/dashboard/summary` endpoint.

### 1.4. Component Refactor & Creation

*   **Refactor `frontend/src/pages/DashboardPage.tsx`:** This component will be refactored to use the new `useDashboardSummary` hook and will pass the fetched data down to new, specialized display components.
*   **New Components:**
    *   `frontend/src/components/Dashboard/SummaryCard.tsx`: A reusable card component to display a single metric (e.g., "Total Value").
    *   `frontend/src/components/Dashboard/TopMoversTable.tsx`: A table component to display the list of top-moving assets.

### 1.5. Note on Backend Data

The frontend will be built to correctly render the current data structure from the backend, including the placeholder values for P&L and top movers. This ensures the UI is ready for when the backend logic is enhanced in the future.