# Feature Plan: Portfolio Page Redesign (FR4.7 & FR4.8)

## 1. Objective

To completely overhaul the Portfolio Detail page based on direct user feedback from the pilot release. The current page, which shows a simple list of raw transactions, is not providing sufficient value. The redesign will transform this page into a powerful analytical tool by replacing the transaction list with a consolidated view of current holdings, adding a high-level portfolio summary, and providing a "drill-down" capability to view the transaction history for each specific holding.

## 2. Functional Requirements

This feature plan addresses requirements **FR4.7** and **FR4.8**.

### 2.1. Portfolio Summary Header (FR4.7.1)

*   **FR-PPR-1.1:** The top of the page must display a prominent summary card or a series of cards.
*   **FR-PPR-1.2:** This summary must contain the following key metrics calculated for the specific portfolio being viewed:
    *   Total Portfolio Value
    *   Total Invested Amount
    *   Day's P&L (in absolute currency and percentage)
    *   Unrealized P&L (in absolute currency and percentage)
    *   Realized P&L

### 2.2. Consolidated Holdings View (FR4.7.2)

*   **FR-PPR-2.1:** The main content area of the page will be replaced with a table displaying a consolidated view of *currently held* assets.
*   **FR-PPR-2.2:** Each row in the table will represent a single asset holding.
*   **FR-PPR-2.3:** The table must include the following columns for each holding:
    *   Asset Name / Ticker
    *   Quantity (total units currently held)
    *   Average Buy Price
    *   Total Invested Amount
    *   Last Traded Price (LTP) / Current Price
    *   Day's Change (%)
    *   Day's P&L
    *   Current Value
    *   Unrealized P&L (Absolute)
    *   Unrealized P&L (%)

### 2.3. Holdings Drill-Down View (FR4.7.3)

*   **FR-PPR-3.1 (Initiation):** Clicking on any row in the Consolidated Holdings View must open a detailed "drill-down" view for that specific asset, either in a modal or an expandable section.
*   **FR-PPR-3.2 (Asset Summary):** The drill-down view must contain a summary section for the asset, including:
    *   Stock Name / Ticker
    *   ISIN
    *   Current Price
    *   Buttons to trigger on-demand calculation of XIRR (current and historical).
*   **FR-PPR-3.3 (Buy Transaction History):** The drill-down must display a list of all *buy* transactions that constitute the current holding (i.e., sold transactions are excluded from this view).
*   **FR-PPR-3.4 (Transaction Actions):** Each transaction row in this detailed view must provide buttons to **Edit** and **Delete** the transaction, linking to the functionality defined in **FR4.4.1**.

### 2.4. Dedicated Transaction History Page (FR4.8)

*   **FR-PPR-4.1:** The full, raw transaction list will be moved from the Portfolio Detail page to a new, dedicated "Transaction History" page or tab.
*   **FR-PPR-4.2:** This new page will provide filtering capabilities by date range, transaction type, and asset.

## 3. Non-Functional Requirements

*   **NFR-PPR-1 (Performance):** Calculations for the summary and holdings view must be performed efficiently on the backend. On-demand calculations (like XIRR) should be triggered explicitly by the user to ensure fast initial page loads.
*   **NFR-PPR-2 (Usability):** The layout must be clean and intuitive, allowing users to easily understand their portfolio's state and drill down for more details.
*   **NFR-PPR-3 (Data Accuracy):** All calculations (Average Buy Price, P&L, etc.) must be precise and thoroughly tested.

## 4. High-Level Technical Design

### 4.1. Backend

*   **New API Endpoints:**
    *   `GET /api/v1/portfolios/{portfolio_id}/summary`: Returns the data for the Portfolio Summary Header.
    *   `GET /api/v1/portfolios/{portfolio_id}/holdings`: Returns the list of consolidated holdings with all calculated metrics.
*   **Business Logic (`crud_portfolio.py` or a new `crud_holdings.py`):**
    *   Significant new business logic will be required to calculate the consolidated holdings. This will involve:
        *   Fetching all transactions for a portfolio.
        *   Iterating through them chronologically to calculate the average cost basis for each asset.
        *   Calculating realized P&L on sell transactions.
        *   Calculating unrealized P&L and current value for remaining holdings based on current market prices.
*   **Database Schema:** No changes are required to the database schema.

### 4.2. Frontend

*   **Page Refactor (`PortfolioDetailPage.tsx`):**
    *   This page will be completely refactored to remove the existing `TransactionList`.
    *   It will orchestrate the new components and fetch data from the new backend endpoints.
*   **New UI Components:**
    *   `PortfolioSummary.tsx`: A component to display the summary cards.
    *   `HoldingsTable.tsx`: A table component to display the consolidated holdings.
    *   `HoldingDetailView.tsx`: A modal or expandable component for the drill-down view. This component will contain the `TransactionList` (filtered for a single asset) and the Edit/Delete buttons.
*   **State Management (React Query):**
    *   New queries will be added to `usePortfolios.ts` to fetch data from the `/summary` and `/holdings` endpoints.
    *   The cache for these new queries must be invalidated whenever a transaction is added, edited, or deleted to ensure the view is always up-to-date.

## 5. User Flow

1.  **User Action:** User navigates to the detail page for one of their portfolios.
2.  **System Action (Frontend):**
    *   The `PortfolioDetailPage` component mounts.
    *   It triggers two API calls via React Query hooks: one to `/summary` and one to `/holdings`.
    *   Loading indicators are displayed while data is being fetched.
3.  **System Action (Backend):**
    *   The backend performs the complex calculations for the summary and holdings.
    *   It returns the two JSON payloads to the frontend.
4.  **System Action (Frontend):**
    *   The `PortfolioSummary` and `HoldingsTable` components render with the fetched data.
5.  **User Action:** User clicks on a specific stock (e.g., "RELIANCE") in the `HoldingsTable`.
6.  **System Action (Frontend):**
    *   The `HoldingDetailView` modal opens.
    *   It displays the detailed summary for "RELIANCE" and a list of its constituent buy transactions.
7.  **User Action:** User clicks the "Edit" button on a specific transaction within the modal.
8.  **System Action (Frontend):** The `TransactionFormModal` opens in "edit" mode, pre-filled with that transaction's data.

## 6. Open Questions

*   **Real-time P&L:** How "real-time" should the Day's P&L be? Will it be based on the last fetched price, or should we implement a mechanism for more frequent updates? (Assumption: For now, it will be based on the price at the time of page load).
*   **Calculation Location:** Should all calculations be done in a single, complex `/holdings` endpoint, or should we have separate, more focused endpoints? (Recommendation: Start with a single endpoint for simplicity, and refactor if performance becomes an issue).