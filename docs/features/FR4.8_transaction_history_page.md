# Feature Plan: Dedicated Transaction History Page (FR4.8)

**Feature ID:** FR4.8
**Title:** Dedicated Transaction History Page
**User Story:** As a user, I want a dedicated page where I can view, filter, edit, and delete all my transactions, so I can easily find specific records, correct mistakes, and analyze my trading history.

---

## 1. Objective

This document outlines the implementation plan for creating a new, dedicated page for viewing and filtering transaction history. This feature will replace the simple transaction list currently on the portfolio detail page with a more powerful, centralized tool.

---

## 2. Backend Implementation Plan

The backend will be enhanced to provide a new, filterable endpoint for transactions.

### 2.1. Database Schema Changes

*   **No database schema changes are required.** All necessary data exists in the current `transactions` and `assets` tables.

### 2.2. New API Endpoint

The transaction API will be enhanced to support full CRUD operations.

*   **Endpoint:** `GET /api/v1/transactions/`
*   **Description:** Fetches a paginated list of all transactions for the currently authenticated user, with optional filters.
*   **Query Parameters:**
    *   `portfolio_id` (optional, `uuid`): Filter by a specific portfolio.
    *   `asset_id` (optional, `uuid`): Filter by a specific asset.
    *   `transaction_type` (optional, `str`): Filter by 'BUY' or 'SELL'.
    *   `start_date` (optional, `str`): ISO 8601 format (e.g., `2025-01-01`).
    *   `end_date` (optional, `str`): ISO 8601 format (e.g., `2025-12-31`).
    *   `skip` (optional, `int`, default: 0): For pagination.
    *   `limit` (optional, `int`, default: 100): For pagination.
*   **Response:** A JSON object containing a list of transactions and total count for pagination.
*   **Endpoint:** `PUT /api/v1/portfolios/{portfolio_id}/transactions/{transaction_id}`
    *   **Description:** Updates an existing transaction.
*   **Endpoint:** `DELETE /api/v1/portfolios/{portfolio_id}/transactions/{transaction_id}`
    *   **Description:** Deletes an existing transaction.

### 2.3. Backend File Changes

*   **`backend/app/api/v1/endpoints/transactions.py`**:
    *   Add the new `GET /` endpoint to the existing router.
    *   Ensure `PUT` and `DELETE` endpoints are implemented and secure.
*   **`backend/app/crud/crud_transaction.py`**:
    *   Implement a new method, `get_multi_by_user_with_filters`, that dynamically builds a SQLAlchemy query based on the provided filter parameters.
*   **`backend/app/schemas/transaction.py`**:
    *   **Fix:** The `TransactionUpdate` schema must be correctly defined with all optional fields.
    *   Create a new `TransactionWithAsset` response schema that includes nested asset details (name, ticker) for a richer display on the frontend.
*   **`backend/app/tests/api/v1/test_transactions.py`**:
    *   Create a new test file to comprehensively test the new filterable endpoint, including all filter combinations and pagination.

---

## 3. Frontend Implementation Plan

A new page will be created to house the transaction history view and its filters.

### 3.1. New Files to Create

*   **Page:** `frontend/src/pages/TransactionsPage.tsx`
*   **Components:**
    *   `frontend/src/components/Transactions/TransactionFilterBar.tsx`
    *   `frontend/src/components/Transactions/TransactionHistoryTable.tsx`
    *   `frontend/src/components/Portfolio/TransactionFormModal.tsx`: **Update** this modal to handle both "create" and "edit" modes.
    *   `frontend/src/components/common/DeleteConfirmationModal.tsx`: A reusable modal for confirming deletions.
    *   `frontend/src/components/common/PaginationControls.tsx`
*   **Data Layer:**
    *   `frontend/src/hooks/useTransactions.ts`
    *   `frontend/src/services/transactionApi.ts`
*   **Types:** `frontend/src/types/transaction.ts` (Update with new response type)

### 3.2. User Flow & UI Components

1.  **Navigation:** A new "Transactions" link will be added to the main `NavBar`.
2.  **`TransactionsPage.tsx`:** This page will be the main container, rendering the filter bar and the history table. It will manage the state for the active filters and pass them to the data-fetching hook.
3.  **`TransactionFilterBar.tsx`:** A dedicated component containing dropdowns for portfolios and assets, radio buttons for transaction type, and date pickers.
4.  **`TransactionHistoryTable.tsx`:** A table to display the filtered transactions. It will include an "Actions" column with "Edit" and "Delete" buttons for each row.
5.  **`TransactionFormModal.tsx`:** When the "Edit" button is clicked, this modal will open, pre-populated with the data for the selected transaction.
6.  **`DeleteConfirmationModal.tsx`:** When the "Delete" button is clicked, this modal will open to confirm the action before proceeding.
5.  **`PaginationControls.tsx`:** A reusable component to handle page navigation for the transaction list.

### 3.3. Data Layer

*   A new `useTransactions` React Query hook will be created. It will accept the filter state as an argument and include it in the `queryKey`. This ensures that React Query automatically re-fetches data when filters change and caches the results for each unique filter combination.
*   New mutations, `useUpdateTransaction` and `useDeleteTransaction`, will be added to the data layer to handle the API calls. On success, they will invalidate the main transactions query to refresh the UI.

### 3.4. Refactoring

*   The existing transaction list on the `PortfolioDetailPage` will be removed. It will be replaced with a "View All Transactions" button that links to the new `/transactions` page, pre-filtered for that specific portfolio.

---

This plan provides a clear, full-stack roadmap for implementing the dedicated transaction history page. Please review the plan. Once you confirm, we can proceed with the implementation.