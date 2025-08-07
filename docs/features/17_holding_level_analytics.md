# Feature Plan: Holding-Level Analytics (FR4.7.3)

## 1. Objective

To enhance the "Holdings Drill-Down View" by implementing on-demand calculation and display of advanced analytics for a single asset holding. This feature directly addresses requirement `FR-PPR-3.2` from the Portfolio Page Redesign plan. The primary metric to be implemented in this phase is the Extended Internal Rate of Return (XIRR).

## 2. Functional Requirements

*   **FR-HLA-1.1 (UI Element):** The `HoldingDetailModal` must include a "Calculate XIRR" button within the asset summary section.
*   **FR-HLA-1.2 (On-Demand Calculation):** Clicking this button will trigger an API call to a new backend endpoint to calculate the XIRR for that specific asset's transaction history within the portfolio.
*   **FR-HLA-1.3 (Display Result):** The modal must display the calculated XIRR value once the calculation is complete.
*   **FR-HLA-1.4 (Loading/Error States):** The UI must show a loading indicator while the calculation is in progress and display a user-friendly error message if the calculation fails.

## 3. High-Level Technical Design

### 3.1. Backend

*   **New API Endpoint:**
    *   `GET /api/v1/portfolios/{portfolio_id}/assets/{asset_id}/analytics`: A new endpoint to calculate and return analytics for a single asset within a portfolio.
*   **New Schema (`schemas/analytics.py`):**
    *   A new `AssetAnalytics` Pydantic model will be created to define the response structure (e.g., `{"xirr": 0.15}`).
*   **New Business Logic (`crud_analytics.py`):**
    *   A new method, `get_asset_analytics`, will be implemented.
    *   This method will fetch all transactions for the specified asset in the portfolio.
    *   It will then use the existing XIRR calculation logic on this filtered set of transactions.
*   **New Tests (`tests/api/v1/test_analytics.py`):**
    *   A new test case will be added to verify the new endpoint and its calculation logic.

### 3.2. Frontend

*   **Component Update (`HoldingDetailModal.tsx`):**
    *   Add a "Calculate XIRR" button.
    *   Add state to manage the loading, error, and result of the XIRR calculation.
    *   Use the new `useAssetAnalytics` hook to fetch data when the button is clicked.
    *   Conditionally render the loading state, error message, or the calculated XIRR value.
*   **New React Query Hook (`hooks/usePortfolios.ts`):**
    *   Create a new `useAssetAnalytics` hook. This will be a `useQuery` hook configured with `enabled: false` so it only runs when manually refetched.
*   **New API Service (`services/portfolioApi.ts`):**
    *   Add a new `getAssetAnalytics` function to call the new backend endpoint.
*   **New Unit Tests (`__tests__/components/Portfolio/HoldingDetailModal.test.tsx`):**
    *   Add new test cases to verify the button's presence, the display of loading/error/success states, and the correct rendering of the calculated XIRR.

## 4. User Flow

1.  **User Action:** User opens the `HoldingDetailModal` for a specific asset.
2.  **System Action (Frontend):** The modal displays the asset summary and transaction history. An inactive "Calculate XIRR" button is visible.
3.  **User Action:** User clicks the "Calculate XIRR" button.
4.  **System Action (Frontend):**
    *   The `useAssetAnalytics` hook is triggered.
    *   A loading indicator (e.g., "Calculating...") appears next to the button.
5.  **System Action (Backend):**
    *   The `/analytics` endpoint for the asset is called.
    *   The backend calculates the XIRR and returns the result.
6.  **System Action (Frontend):**
    *   The hook receives the data.
    *   The loading indicator is replaced with the calculated XIRR value (e.g., "XIRR: 15.25%").