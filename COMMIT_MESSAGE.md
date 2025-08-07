feat(portfolio): Implement holdings drill-down view

This commit implements the "Holdings Drill-Down View" (FR4.7.3), allowing users to click on any holding to see a detailed breakdown of its constituent transactions. This completes a key part of the portfolio page redesign.

### Backend Changes:
- **New Endpoint:** Created `GET /portfolios/{portfolio_id}/assets/{asset_id}/transactions` to fetch all transactions for a specific asset within a portfolio.
- **New CRUD Method:** Added `get_multi_by_portfolio_and_asset` to `crud_transaction.py` to support the new endpoint.

### Frontend Changes:
- **New Component (`HoldingDetailModal.tsx`):** A new modal that displays a summary of the selected holding and a detailed list of its transactions.
- **FIFO Logic:** Implemented First-In, First-Out (FIFO) logic in the modal to accurately display only the "open" buy transactions that make up the current holding.
- **CAGR Calculation:** Added a "CAGR %" column to the transaction list for quick, on-the-fly performance analysis of each buy lot.
- **UI/UX Polish:** Iteratively fixed multiple UI defects in the modal, including spacing, borders, and button visibility, based on manual E2E testing feedback.
- **Data Layer:** Added the `useAssetTransactions` hook and `getAssetTransactions` API service function.
- **Page Integration:** Updated `PortfolioDetailPage.tsx` to manage the state and rendering of the new drill-down modal.
- **Test Suite:** Added a comprehensive unit test suite for `HoldingDetailModal.tsx`, including tests for the FIFO logic and UI states. Stabilized existing tests to align with the new functionality.
