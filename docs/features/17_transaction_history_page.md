# Feature Plan: Dedicated Transaction History Page (FR4.8)

## 1. Objective

To provide users with a dedicated, comprehensive view of all their historical transactions for a specific portfolio. This page will replace the raw transaction list that was previously part of the portfolio detail page and will add powerful filtering capabilities to allow users to easily find and analyze specific transactions.

## 2. Functional Requirements (from FR4.8)

*   **FR4.8.1:** A separate, dedicated page must be created to display the full, raw transaction list for a portfolio.
*   **FR4.8.2:** By default, this page must only show transactions for the current financial year.
*   **FR4.8.3:** The page must include filters to view historical transactions by date range, transaction type (BUY/SELL), and asset.

## 3. High-Level Technical Design

### 3.1. Backend (API & Logic)

**Role:** Backend Developer

#### 3.1.1. API Endpoint

A new endpoint will be created to fetch transactions for a portfolio with optional filtering.

*   **Endpoint:** `GET /api/v1/portfolios/{portfolio_id}/transactions`
*   **Query Parameters:**
    *   `start_date` (string, optional, format: `YYYY-MM-DD`)
    *   `end_date` (string, optional, format: `YYYY-MM-DD`)
    *   `transaction_type` (string, optional, values: `BUY` or `SELL`)
    *   `asset_id` (UUID, optional)
*   **Success Response (200 OK):**
    ```json
    {
      "transactions": [
        {
          "id": "uuid",
          "transaction_date": "YYYY-MM-DD",
          "asset": { "id": "uuid", "ticker_symbol": "RELIANCE.NS", "name": "Reliance Industries" },
          "transaction_type": "BUY",
          "quantity": 10,
          "price_per_unit": 2500.00,
          "fees": 50.00
        }
      ]
    }
    ```

#### 3.1.2. Business Logic (CRUD)

*   A new method will be added to `backend/app/crud/crud_transaction.py`: `get_all_by_portfolio_with_filters()`.
*   This method will build a dynamic SQLAlchemy query based on the provided filter parameters.
*   It will join with the `Asset` model to include asset details in the response.
*   The default date range will be the current financial year (April 1st of the current/previous year to March 31st of the current/next year).

#### 3.1.3. Proposed File Changes

*   **Update:** `backend/app/api/v1/endpoints/portfolios.py` - Add the new `GET /{portfolio_id}/transactions` endpoint.
*   **Update:** `backend/app/crud/crud_transaction.py` - Add the new `get_all_by_portfolio_with_filters` method.
*   **New:** `backend/app/tests/api/v1/test_transaction_history.py` - A new test suite for the transaction history endpoint, covering all filter combinations.

### 3.2. Frontend (UI & State)

**Role:** Frontend Developer

#### 3.2.1. UI/UX Flow

1.  A "View All Transactions" link/button will be added to the `PortfolioDetailPage`.
2.  Clicking this link navigates the user to the new `TransactionHistoryPage` (`/portfolios/{id}/transactions`).
3.  The page displays a filter bar at the top and a table of transactions below.
4.  By default, the table shows transactions for the current financial year.
5.  The user can change the filters (e.g., select a different date range, filter by asset).
6.  As filters change, the transaction table automatically re-fetches data and updates.

#### 3.2.2. Components

*   **`TransactionHistoryPage.tsx`:** The main page component. It will manage the state of the filters and use a React Query hook to fetch the data.
*   **`TransactionFilterBar.tsx`:** A new component containing the filter inputs:
    *   Date range picker.
    *   Dropdown for transaction type (All, BUY, SELL).
    *   An autocomplete/searchable dropdown to select an asset from the user's portfolio.
*   **`FullTransactionTable.tsx`:** A new component to display the list of transactions. It will be similar to the old transaction list but will include columns for all relevant data.

#### 3.2.3. Data Layer

*   A new React Query hook, `usePortfolioTransactions`, will be created in `frontend/src/hooks/usePortfolios.ts`. This hook will accept the filter state as an argument and pass it to the API call.
*   A new API service function, `getPortfolioTransactions`, will be added to `frontend/src/services/portfolioApi.ts`.

#### 3.2.4. Proposed File Changes

*   **New:** `frontend/src/pages/Portfolio/TransactionHistoryPage.tsx`
*   **New:** `frontend/src/components/Portfolio/TransactionFilterBar.tsx`
*   **New:** `frontend/src/components/Portfolio/FullTransactionTable.tsx`
*   **Update:** `frontend/src/hooks/usePortfolios.ts` - Add `usePortfolioTransactions` hook.
*   **Update:** `frontend/src/services/portfolioApi.ts` - Add `getPortfolioTransactions` function.
*   **Update:** `frontend/src/pages/Portfolio/PortfolioDetailPage.tsx` - Add a link to the new history page.
*   **Update:** `frontend/src/App.tsx` - Add the new route for the history page.
*   **New:** `frontend/src/__tests__/pages/Portfolio/TransactionHistoryPage.test.tsx` - New test suite.

## 4. Testing Plan

**Role:** QA Engineer

*   **Backend:**
    *   Test the new endpoint with no filters (should return current financial year's data).
    *   Test with each filter individually (`start_date`, `end_date`, `transaction_type`, `asset_id`).
    *   Test with combinations of filters.
    *   Test with invalid filter values.
*   **Frontend:**
    *   Test that the `TransactionHistoryPage` renders correctly and fetches initial data.
    *   Test that each filter component works correctly.
    *   Test that changing a filter triggers a re-fetch and updates the table.
*   **E2E:**
    *   Create a new E2E test that navigates from the portfolio detail page to the transaction history page.
    *   The test will apply a filter (e.g., by asset) and assert that the transaction table updates to show only the expected transactions.