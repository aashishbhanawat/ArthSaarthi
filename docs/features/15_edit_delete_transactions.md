# Feature Plan: Edit & Delete Transactions (FR4.4.1)

**Status: ✅ Done**
---

## 1. Objective

To provide users with the critical ability to edit and delete existing transactions. This feature directly addresses pilot feedback where users reported needing a way to correct data entry mistakes (e.g., incorrect transaction type, quantity, or price) to maintain the accuracy of their portfolio data.

## 2. Functional Requirements

### 2.1. Edit Transaction

*   **FR-EDIT-1.1 (Initiation):** Users must be able to initiate an "Edit" action for a specific transaction from the transaction list view.
*   **FR-EDIT-1.2 (UI):**
    *   Activating the "Edit" action must open a modal dialog.
    *   This modal must be pre-populated with all the data from the selected transaction (Asset, Type, Quantity, Price, Date, Fees).
    *   The modal's appearance and layout should be consistent with the existing "Add Transaction" modal.
*   **FR-EDIT-1.3 (Submission):**
    *   Upon saving, the frontend must send the updated data to the backend.
    *   The backend must validate the updated transaction. For example, changing a BUY to a SELL must trigger the same holding validation logic as creating a new SELL transaction.
*   **FR-EDIT-1.4 (Feedback):** After a successful update, the modal must close, and the transaction list in the UI must immediately reflect the changes without requiring a manual page refresh.

### 2.2. Delete Transaction

*   **FR-DELETE-1.1 (Initiation):** Users must be able to initiate a "Delete" action for a specific transaction from the transaction list view.
*   **FR-DELETE-1.2 (Confirmation):**
    *   To prevent accidental data loss, activating the "Delete" action must open a confirmation modal.
    *   The modal must clearly state which transaction is about to be deleted.
*   **FR-DELETE-1.3 (Submission):** Upon user confirmation, the frontend must send a request to the backend to permanently delete the transaction.
*   **FR-DELETE-1.4 (Feedback):** After a successful deletion, the confirmation modal must close, and the transaction must be removed from the list in the UI without requiring a manual page refresh.

## 3. Non-Functional Requirements

*   **NFR-ED-1 (Security):** A user must only be able to edit or delete transactions that they own. The backend must enforce this ownership check.
*   **NFR-ED-2 (Data Integrity):** Any edit or delete operation must trigger a recalculation of all relevant portfolio and dashboard analytics (e.g., holdings, P/L, XIRR) to ensure data consistency across the application.
*   **NFR-ED-3 (Usability):** The edit and delete actions should be intuitive, with clear icons or buttons. The process should provide immediate visual feedback.

## 4. High-Level Technical Design

### 4.1. Backend

*   **API Endpoints (New):**
    *   `PUT /api/v1/transactions/{transaction_id}`: Updates a specific transaction.
    *   `DELETE /api/v1/transactions/{transaction_id}`: Deletes a specific transaction.
*   **CRUD Logic (`crud_transaction.py`):**
    *   The existing `update` and `remove` methods in the `CRUDBase` class will be utilized.
    *   The `update` endpoint logic will need to be enhanced to perform the same validation as the `create` logic, especially if the quantity or transaction type is changed.
*   **Database Schema:** No changes are required to the database schema.

### 4.2. Frontend

*   **UI Components:**
    *   **Transaction List:** The component displaying the list of transactions will be updated to include "Edit" and "Delete" buttons/icons for each row.
    *   **Edit Modal:** The existing `AddTransactionModal.tsx` will be refactored into a more generic `TransactionFormModal.tsx` that can handle both "create" and "edit" modes.
    *   **Delete Modal:** A generic `DeleteConfirmationModal.tsx` will be used to confirm the delete action.
*   **State Management (React Query):**
    *   **Mutations:** New mutations will be created in `usePortfolios.ts` (or a new `useTransactions.ts` hook) for `updateTransaction` and `deleteTransaction`.
    *   **Cache Invalidation:** On successful mutation (`onSuccess`), the following queries must be invalidated to trigger a UI refresh with the new data:
        *   `['portfolio', portfolioId]`
        *   `['dashboardSummary']`
        *   `['dashboardHistory']`
        *   `['dashboardAllocation']`
        *   `['portfolioAnalytics', portfolioId]`

## 5. User Flow

### 5.1. Edit Transaction Flow

1.  **User Action:** User clicks the "Edit" icon next to a transaction in the list.
2.  **System Action (Frontend):**
    *   The `TransactionFormModal` opens in "edit" mode.
    *   A query is made to fetch the specific transaction's details (if not already available).
    *   The form is pre-filled with the transaction's data.
3.  **User Action:** User modifies the data (e.g., changes the quantity) and clicks "Save Changes".
4.  **System Action (Frontend):** The `updateTransaction` mutation is called with the new data.
5.  **System Action (Backend):** The `PUT /api/v1/transactions/{id}` endpoint validates and updates the transaction in the database.
6.  **System Action (Frontend):** On success, the modal closes, and the relevant React Query caches are invalidated, causing the transaction list and analytics to update automatically.

### 5.2. Delete Transaction Flow

1.  **User Action:** User clicks the "Delete" icon next to a transaction.
2.  **System Action (Frontend):** The `DeleteConfirmationModal` opens, displaying a confirmation message.
3.  **User Action:** User clicks the "Confirm Delete" button.
4.  **System Action (Frontend):** The `deleteTransaction` mutation is called.
5.  **System Action (Backend):** The `DELETE /api/v1/transactions/{id}` endpoint deletes the transaction from the database.
6.  **System Action (Frontend):** On success, the modal closes, and the relevant React Query caches are invalidated, causing the transaction to disappear from the list and analytics to update.