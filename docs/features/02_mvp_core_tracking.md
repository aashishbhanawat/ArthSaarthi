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

**Transaction Endpoints (for FR4)**
*   `POST /api/v1/transactions`: Adds a new transaction to a specified portfolio.
*   `PUT /api/v1/transactions/{transaction_id}`: Updates an existing transaction.
*   `DELETE /api/v1/transactions/{transaction_id}`: Deletes a transaction.

**Dashboard Data Endpoints (for FR3)**
*   `GET /api/v1/dashboard/summary`: An endpoint to get aggregated KPI data (Total Value, P/L, etc.) for the user's entire holdings.

### 1.3. Backend Logic Overview

*   **Authorization:** All endpoints will be protected. Admin endpoints will require an `is_admin=True` check. All other endpoints will be scoped to the `user_id` of the requester.
*   **Asset Handling:** When a transaction is added for a new ticker symbol, the backend will:
    1.  Check if the asset exists in the `assets` table.
    2.  If not, it will call the external financial data API (**FR5**) to fetch the asset's full name and other details.
    3.  It will then create a new record in the `assets` table before creating the transaction record.
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
    *   `admin.py`, `portfolios.py`, `transactions.py`, `dashboard.py`
*   **Services (`app/services/`):**
    *   `financial_data_service.py`: A new service to abstract the logic for communicating with the third-party financial data API.

---