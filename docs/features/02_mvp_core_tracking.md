# Feature Plan: MVP Core Portfolio Tracking

This document outlines the backend development plan for the core portfolio and transaction management features of the MVP.

**Related Requirements:** FR2, FR3 (data endpoints), FR4 (core), FR5

## 1. Backend Development Plan

This plan was created by the **Backend Developer** and **Database Administrator**.

### 1.1. Database Schema

This feature will utilize the `portfolios`, `assets`, and `transactions` tables as defined in `docs/mvp_database_schema.md`. All queries will be strictly scoped to the authenticated `user_id` to ensure data privacy.

### 1.2. API Endpoints (FastAPI)

**Admin Endpoints (for FR2)**
*   `POST /api/v1/admin/users`: Creates a new standard user. Requires admin privileges.
*   `GET /api/v1/admin/users`: Lists all users. Requires admin privileges.
*   `DELETE /api/v1/admin/users/{user_id}`: Deletes a user. Requires admin privileges.

**Portfolio Endpoints (for FR4)**
*   `POST /api/v1/portfolios`: Creates a new portfolio for the current user.
*   `GET /api/v1/portfolios`: Gets all portfolios for the current user.
*   `GET /api/v1/portfolios/{portfolio_id}`: Gets a single portfolio with its associated assets and transactions.
*   `DELETE /api/v1/portfolios/{portfolio_id}`: Deletes a portfolio.

**Asset & Transaction Endpoints (for FR4)**
*   `GET /api/v1/assets/lookup/{ticker_symbol}`: A new endpoint that allows the frontend to look up asset details from the external financial API. This keeps API keys and external communication on the backend. It will return the asset details if found, or a 404 if not.
*   `POST /api/v1/assets/`: Creates a new asset in the local database after validating the ticker against the external financial API.
*   `POST /api/v1/portfolios/{portfolio_id}/transactions/`: Adds a new transaction to a specified portfolio. This endpoint is nested under the portfolio it belongs to.

**Dashboard Data Endpoints (for FR3)**
*   `GET /api/v1/dashboard/summary`: An endpoint to get aggregated KPI data (Total Value, P/L, etc.) for the user's entire holdings.

### 1.3. Backend Logic Overview

*   **Authorization:** All endpoints will be protected. Admin endpoints will require an `is_admin=True` check. All other endpoints will be scoped to the `user_id` of the requester, ensuring users can only access their own data.
*   **Asset & Transaction Handling:** The logic for adding a transaction is now a multi-step, robust process to ensure data integrity.
    1.  The frontend first uses `GET /api/v1/assets/lookup/` to search for an existing asset in the local database.
    2.  If the asset is not found, the frontend allows the user to trigger a call to `POST /api/v1/assets/`. This endpoint validates the ticker against the external financial service. If valid, it creates the new asset in the local database and returns it.
    3.  With a valid `asset_id` (either from the lookup or the creation step), the frontend then calls `POST /api/v1/portfolios/{portfolio_id}/transactions/` to create the transaction.
    4.  The backend validates that the user owns the portfolio and has sufficient holdings for `SELL` transactions.
*   **Dashboard Calculations:** The `/dashboard/summary` endpoint will perform aggregations across all of the user's transactions and fetch the latest market prices from the external API to provide up-to-date summary figures.

### 1.4. Proposed Backend File Structure

This is an extension of the file structure proposed for user authentication.

*   **Models (`app/models/`):**
    *   `portfolio.py`, `asset.py`, `transaction.py`
*   **Schemas (`app/schemas/`):**
    *   `portfolio.py`, `asset.py`, `transaction.py`, `dashboard.py`
*   **CRUD (`app/crud/`):**
    *   `crud_portfolio.py`, `crud_asset.py`, `crud_transaction.py`
*   **API Endpoints (`app/api/v1/endpoints/`):**
    *   `admin.py`, `portfolios.py` (which now includes transaction routing), `dashboard.py`, `assets.py`
*   **Services (`app/services/`):**
    *   `financial_data_service.py`: A new service to abstract the logic for communicating with the third-party financial data API.

---

## 2. Frontend Development Plan

This plan was created by the **Frontend Developer** and **UI/UX Designer**.

### 2.1. UI/UX Flow: "Add Transaction" Modal

To provide a smooth user experience, the "Add Transaction" flow will handle both automatic and manual asset data entry.

1.  **User Action:** The user clicks "Add Transaction" and a modal opens.
2.  **Ticker Input:** The user enters a ticker symbol (e.g., "AAPL").
3.  **Automatic Search:** A debounced search calls `GET /api/v1/assets/lookup/` to show a list of matching, existing assets.
4.  **Asset Selection:** The user can select an asset from the search results.
5.  **New Asset Creation:** If no asset is found, a "Create new asset" button appears. Clicking it calls `POST /api/v1/assets/` to validate and create the asset. On success, the new asset is selected.
6.  **Submission:** The user fills in the remaining transaction details (quantity, price, date) and submits the form. The payload is sent to `POST /api/v1/portfolios/{portfolio_id}/transactions/`.

### 2.2. State Management & API Integration

*   **State Management:** We will use **React Query** to manage the server state, including the asset lookup query and the transaction creation mutation. This will handle loading, success, and error states gracefully.
*   **API Integration:** A service file, `frontend/src/services/portfolioApi.ts`, will be created to interact with the portfolio, asset, and transaction endpoints.

### 2.3. Proposed Frontend File Structure

*   `frontend/src/pages/Portfolio/PortfolioPage.tsx`: Main page to display a user's portfolios.
*   `frontend/src/components/Portfolio/TransactionList.tsx`: Component to display a table of transactions for a given portfolio.
*   `frontend/src/components/Portfolio/AddTransactionModal.tsx`: The modal component implementing the smart form logic described in the UI/UX flow.
---