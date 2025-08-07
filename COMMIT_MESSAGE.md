feat(portfolio): Complete full-stack portfolio page redesign with sorting

This commit delivers the full-stack implementation of the "Portfolio Page Redesign" feature (FR4.7), a major enhancement driven by pilot user feedback. The portfolio detail page has been transformed from a simple transaction list into a modern, insightful dashboard with interactive sorting capabilities.

### Frontend Changes:
- **Refactored Page (`PortfolioDetailPage.tsx`):** Replaced the old transaction list with the new `PortfolioSummary` and `HoldingsTable` components.
- **New Components:**
    - `PortfolioSummary.tsx`: Displays key metrics in a series of summary cards.
    - `HoldingsTable.tsx`: Displays the detailed, consolidated list of current asset holdings. This table now includes client-side sorting on all columns, defaulting to sort by "Current Value" descending.
- **New Data Layer:** Added new types, API service functions, and React Query hooks (`usePortfolioSummary`, `usePortfolioHoldings`) to consume the new backend endpoints.
- **New Unit Tests:** Added dedicated unit tests for the `PortfolioSummary` and `HoldingsTable` components, including tests for the new sorting functionality.
- **E2E Test Suite Stabilization:** The entire E2E test suite was updated to align with the new UI. Obsolete tests were removed, and existing tests were refactored to assert against the new consolidated holdings view instead of the old transaction list.
