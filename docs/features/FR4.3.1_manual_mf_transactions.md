# Feature Plan: Manual Mutual Fund Transaction Management (FR4.3.1)

**Status: ✅ Done**
---

**Feature ID:** FR4.3.1
**Title:** Add Manual Indian Mutual Fund Transaction Support
**User Story:** As a user, I want to manually add my Indian Mutual Fund transactions by searching for the fund by name or scheme code, so that I can accurately track my MF portfolio.

---

## 1. Objective

The current system has basic support for Mutual Funds (MFs), but it relies on `yfinance`, which is unreliable for fetching Net Asset Values (NAVs) for Indian MFs. This feature will enhance the system to robustly handle manual MF transactions by integrating a reliable data source for Indian MFs and providing a user-friendly search interface.

This work is a prerequisite for automating MF transaction imports (FR7.1.2).

---

## 2. Technical Design & Architecture

### 2.1. Backend

1.  **New Data Source for NAVs:**
    *   A new data provider, `AmfiIndiaProvider`, will be created within `backend/app/services/financial_data_service.py`.
    *   This provider will be responsible for fetching, parsing, and caching the daily NAV report text file from the AMFI (Association of Mutual Funds in India) website. This is a public and reliable data source.
    *   The NAV data will be cached daily to avoid excessive network requests. The existing pluggable cache layer (`diskcache` or `redis`) will be used.

2.  **Financial Data Service Refactor:**
    *   The `get_asset_price` method in `financial_data_service.py` will be updated. If the requested `asset_type` is `MUTUAL_FUND`, it will use the new `AmfiIndiaProvider`. For all other asset types, it will fall back to the existing `yfinance` provider.

3.  **New API Endpoint for MF Search:**
    *   A new endpoint `GET /api/v1/assets/search-mf` will be created.
    *   This endpoint will accept a query parameter `q` (e.g., `/search-mf?q=axis`).
    *   It will search the cached AMFI data for matching Mutual Fund schemes by name or scheme code and return a list of results.

4.  **Asset Creation Enhancement:**
    *   The existing `POST /api/v1/assets/` endpoint (which is called when a transaction for a new ticker is added) will be enhanced.
    *   When a new asset of type `MUTUAL_FUND` is created, the system will use the provided `ticker_symbol` (which will be the MF Scheme Code) to look up the full fund name and ISIN from the cached AMFI data, ensuring the asset is created with accurate details.

### 2.2. Frontend

1.  **"Add Transaction" Modal Enhancement:**
    *   The `AddTransactionModal.tsx` component will be updated.
    *   When the user selects "Mutual Fund" as the asset type, the "Asset" input field will transform into a search component.
    *   This component will use a new React Query hook, `useMfSearch`, to call the `/api/v1/assets/search-mf` endpoint as the user types.
    *   Search results (e.g., "Axis Bluechip Fund - 100001") will be displayed in a dropdown.
    *   When the user selects a fund, the modal will use the fund's **Scheme Code** as the `ticker_symbol` for the transaction payload.

---

## 3. Implementation Plan

This feature will be implemented in a backend-first approach.

### 3.1. Backend Development

1.  **Create `AmfiIndiaProvider`:**
    *   In `financial_data_service.py`, create a new class `AmfiIndiaProvider`.
    *   Implement a method to download the NAV text file from the AMFI website URL (`https://www.amfiindia.com/spages/NAVAll.txt`).
    *   Implement a method to parse this text file. It is a semi-colon delimited format. The parser should extract `Scheme Code`, `ISIN`, `Scheme Name`, and `Net Asset Value`.
    *   Implement a caching layer for the parsed data with a 24-hour TTL.
2.  **Update `FinancialDataService`:**
    *   Modify `get_asset_price` to delegate to `AmfiIndiaProvider` for `MUTUAL_FUND` assets.
3.  **Create Search Endpoint:**
    *   Create the `GET /api/v1/assets/search-mf` endpoint in a new file `backend/app/api/v1/endpoints/assets.py` (if it doesn't exist) or update it.
    *   The endpoint logic will perform a case-insensitive search on the cached AMFI data.
4.  **Update Asset Creation Endpoint:**
    *   In `crud_asset.py`, modify the `get_or_create` method. If the asset type is `MUTUAL_FUND`, use the `AmfiIndiaProvider` to fetch the full name and ISIN before creating the new asset record.
5.  **Add Unit Tests:**
    *   Create `backend/app/tests/services/test_amfi_provider.py`.
    *   Add tests for the new search endpoint in `backend/app/tests/api/v1/test_assets.py`.
    *   Add tests to `test_transactions.py` to verify the creation of a new MF asset via a transaction.

### 3.2. Frontend Development

1.  **Create `useMfSearch` Hook:**
    *   In `frontend/src/hooks/useAssets.ts`, add a new `useMfSearch` hook that uses React Query's `useQuery` to fetch data from the new search endpoint, with debouncing on the user input.
2.  **Update `AddTransactionModal.tsx`:**
    *   Conditionally render a search input/dropdown component (e.g., using a library like `react-select`) when the asset type is "Mutual Fund".
    *   Wire up this component to the `useMfSearch` hook.
    *   On selection, populate the form state with the chosen fund's scheme code.
3.  **Update Unit Tests:**
    *   Update tests for `AddTransactionModal.test.tsx` to cover the new search and selection functionality.

---

## 5. Implementation Notes

This feature was successfully implemented and is now a core part of the transaction management workflow.

*   **Backend:** The `AmfiIndiaProvider` was created and integrated into the `FinancialDataService`. The service now correctly dispatches requests to either the AMFI provider (for current NAVs) or the yfinance provider (for stocks). The `/api/v1/assets/search-mf/` endpoint is fully functional.
*   **Frontend:** The `TransactionFormModal` was enhanced with a `react-select` component that appears when the "Mutual Fund" asset type is chosen. The `useMfSearch` hook provides debounced search results to this component, creating a seamless user experience.
*   **Historical Data:** A significant enhancement was made during implementation. A public API (`mfapi.in`) was discovered and integrated to provide historical NAV data for mutual funds. This allows the application to perform accurate XIRR calculations for MF holdings, a feature that was not in the original plan.
*   **Testing:** The feature is covered by backend unit tests (`test_amfi_provider.py`), frontend component tests (`TransactionFormModal.test.tsx`), and a dedicated E2E test case (`should allow adding a mutual fund transaction` in `portfolio-and-dashboard.spec.ts`).

This feature is considered complete and stable.

## 4. Testing Plan

*   **Backend:** Unit tests will verify the AMFI data parsing, caching, price lookups, and asset creation.
*   **Frontend:** Component tests will verify the new search functionality in the "Add Transaction" modal.
*   **E2E:** A new test case will be added to `e2e/tests/portfolio-and-dashboard.spec.ts` to cover the full user flow of manually adding a transaction for an Indian Mutual Fund.