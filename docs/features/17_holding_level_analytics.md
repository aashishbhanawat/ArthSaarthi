**Feature ID:** FR4.7.3
**Title:** Display Asset-Level Analytics in Holdings Drill-Down
**User Story:** As a user, I want to see the realized and unrealized XIRR for each of my individual holdings so that I can better understand the performance of specific assets within my portfolio.

## 1. Functional Requirements

-   When a user clicks on a holding in the "Consolidated Holdings View" on the Portfolio Detail page, the "Holdings Drill-Down" modal will open.
-   This modal will now include a new "Performance (XIRR)" section.
-   This section will display two new metrics for the selected asset:
    -   **Realized XIRR:** The annualized return on all closed (sold) lots for that asset.
    -   **Unrealized XIRR:** The annualized return on all open (currently held) lots, calculated against the current market price.
-   Values will be displayed as percentages, formatted to two decimal places (e.g., `43.86%`).
-   If the analytics data is still loading, a loading indicator will be shown.
-   If there is an error fetching the data, an appropriate error message will be displayed.

## 2. Technical Design

### 2.1. Backend (Already Implemented)

-   The `GET /api/v1/portfolios/{portfolio_id}/assets/{asset_id}/analytics` endpoint provides the necessary `realized_xirr` and `unrealized_xirr` values.

### 2.2. Frontend

1.  **Data Layer:**
    -   Create a new `frontend/src/types/analytics.ts` file to define the `AssetAnalytics` interface.
    -   Update `frontend/src/services/portfolioApi.ts` to add a `getAssetAnalytics` function that calls the new backend endpoint.
    -   Update `frontend/src/hooks/usePortfolios.ts` to add a new `useAssetAnalytics` React Query hook.

2.  **UI Layer:**
    -   Refactor `HoldingDetailModal.tsx` to:
        -   Accept a `portfolioId` prop.
        -   Call the new `useAssetAnalytics` hook using the `portfolioId` and the `holding.asset_id`.
        -   Render a new section to display the fetched analytics data, including loading and error states.

3.  **Integration:**
    -   Update `PortfolioDetailPage.tsx` to pass the `portfolioId` to the `HoldingDetailModal`.

4.  **Testing:**
    -   Update `HoldingDetailModal.test.tsx` to mock the new `useAssetAnalytics` hook and verify that the analytics data is rendered correctly in all states (loading, error, success).

## 3. Acceptance Criteria

-   The Holdings Drill-Down modal displays Realized and Unrealized XIRR.
-   The values are formatted as percentages.
-   The modal handles loading and error states gracefully.
-   All related unit tests pass.