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

**Asset Endpoints**
*   `GET /api/v1/assets/lookup/{ticker_symbol}`: A new endpoint that allows the frontend to look up asset details from the external financial API. This keeps API keys and external communication on the backend. It will return the asset details if found, or a 404 if not.

**Transaction Endpoints (for FR4)**
*   `POST /api/v1/transactions`: Adds a new transaction to a specified portfolio.
*   `PUT /api/v1/transactions/{transaction_id}`: Updates an existing transaction.
*   `DELETE /api/v1/transactions/{transaction_id}`: Deletes a transaction.

**Dashboard Data Endpoints (for FR3)**
*   `GET /api/v1/dashboard/summary`: An endpoint to get aggregated KPI data (Total Value, P/L, etc.) for the user's entire holdings.

### 1.3. Backend Logic Overview

*   **Authorization:** All endpoints will be protected. Admin endpoints will require an `is_admin=True` check. All other endpoints will be scoped to the `user_id` of the requester.
*   **Asset & Transaction Handling (`POST /api/v1/transactions`):** The logic for adding a transaction is designed to be flexible and robust.
    *   The request schema will allow for either an existing `asset_id` or a new asset payload (containing `ticker_symbol`, `name`, `asset_type`, `currency`).
    *   If an `asset_id` is provided, the system validates that it belongs to the user and creates the transaction.
    *   If new asset details are provided, the system first checks if an asset with that ticker already exists. If not, it creates a new record in the `assets` table. Then, it proceeds to create the transaction record linked to the new or existing asset.
    *   This approach centralizes the creation logic on the backend while giving the frontend the flexibility to either use existing assets or provide data for new ones, especially when the external lookup fails.
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
    *   `admin.py`, `portfolios.py`, `transactions.py`, `dashboard.py`, `assets.py` (for the new lookup endpoint)
*   **Services (`app/services/`):**
    *   `financial_data_service.py`: A new service to abstract the logic for communicating with the third-party financial data API.

---

## 2. Frontend Development Plan

This plan was created by the **Frontend Developer** and **UI/UX Designer**.

### 2.1. UI/UX Flow: "Add Transaction" Modal

To provide a smooth user experience, the "Add Transaction" flow will handle both automatic and manual asset data entry.

1.  **User Action:** The user clicks "Add Transaction" and a modal opens.
2.  **Ticker Input:** The user enters a ticker symbol (e.g., "AAPL").
3.  **Automatic Lookup:** On blur, the frontend calls the new `GET /api/v1/assets/lookup/{ticker_symbol}` endpoint.
4.  **Success Scenario:** If the backend returns asset details, the "Asset Name" and "Asset Type" fields are auto-populated and made read-only.
5.  **Failure Scenario:** If the backend returns a 404 Not Found, the "Asset Name" and "Asset Type" fields become enabled, allowing the user to enter the details manually. A small helper text will appear (e.g., "Asset not found. Please enter details manually.").
6.  **Submission:** The user fills in the remaining transaction details (quantity, price, date) and submits the form. The payload sent to `POST /api/v1/transactions` will contain all the necessary information for the backend to create the asset (if new) and the transaction.

### 2.2. State Management & API Integration

*   **State Management:** We will use **React Query** to manage the server state, including the asset lookup query and the transaction creation mutation. This will handle loading, success, and error states gracefully.
*   **API Integration:** A new service file, `frontend/src/services/portfolioApi.ts` (or similar), will be created to interact with the portfolio, asset, and transaction endpoints.

### 2.3. Proposed Frontend File Structure

*   `frontend/src/pages/Portfolio/PortfolioPage.tsx`: Main page to display a user's portfolios.
*   `frontend/src/components/Portfolio/TransactionList.tsx`: Component to display a table of transactions for a given portfolio.
*   `frontend/src/components/Portfolio/AddTransactionModal.tsx`: The modal component implementing the smart form logic described in the UI/UX flow.
---