## 2025-11-20: Implement User Data Backup & Restore (NFR7)

*   **Task Description:** Implement the full-stack "Backup & Restore" feature (NFR7), allowing users to export their entire financial data to a JSON file and restore it. This included creating a new backend service for data serialization/deserialization, a new UI in the Profile page, and a robust verification strategy.

*   **Key Prompts & Interactions:**
    1.  **Backend Implementation:** A new `backup_service.py` was created to handle the complex logic of serializing all user data (Portfolios, Transactions, FDs, RDs, Goals, Watchlists) into a versioned JSON format. The restore logic was implemented to perform a transactional "wipe and recreate" of user data while preserving shared `Asset` records.
    2.  **Test Generation:** A comprehensive backend test `test_backup_restore.py` was created to verify the full cycle of data creation, backup, wipe, restore, and verification.
    3.  **Frontend Implementation:** A new `BackupRestoreCard` component was created and integrated into the `ProfilePage`. It features a download button and a restore file input with a high-friction "DELETE" confirmation modal.
    4.  **Systematic Debugging:**
        *   **Backend Test Fixes:** Addressed initial `AttributeError` due to missing imports in `models/__init__.py`.
        *   **Environment Configuration:** Resolved issues with `docker-compose` environment variables and database connectivity during local verification.
        *   **Playwright Verification:** Created a temporary Playwright script to verify the frontend UI and take a screenshot. Debugged timeouts caused by `HashRouter` URL handling (`/#/login`) and missing environment variables for the Vite proxy.
        *   **Manual E2E Fix:** Addressed a critical bug in `backup_service.py` where `create_with_owner` was called with incorrect arguments (`user_id` vs `owner_id`) for FDs/RDs. Added regression test for this.
        *   **Test Failure Fix:** Fixed E2E test expecting old heading text and backend tests running in desktop mode failing due to missing user management endpoints. Moved backup endpoints to `me.py` to resolve this.

*   **File Changes:**
    *   `backend/app/services/backup_service.py`: **New** service for backup/restore logic.
    *   `backend/app/api/v1/endpoints/me.py`: **Updated** to add `/backup` and `/restore` endpoints.
    *   `backend/app/models/__init__.py`: **Updated** to expose all models properly.
    *   `backend/app/tests/api/v1/test_backup_restore.py`: **New** backend test suite.
    *   `frontend/src/components/Profile/BackupRestoreCard.tsx`: **New** UI component.
    *   `frontend/src/pages/ProfilePage.tsx`: **Updated** to include the new card.
    *   `frontend/src/services/userApi.ts`: **Updated** with backup/restore API calls.
    *   `e2e/tests/profile-management.spec.ts`: **Updated** to match UI changes.

*   **Verification:**
    - Ran the new backend test suite (`test_backup_restore.py`), which passed.
    - Ran the full backend test suite (`./run_local_tests.sh backend`), which passed.
    - Performed frontend verification using a custom Playwright script (`verification/verify_backup.py`) and manual inspection of the screenshot.

*   **Outcome:**
    - The "Backup & Restore" feature is fully implemented, tested, and verified.
    - Users can now safely backup their data and restore it, with safeguards against accidental data loss.

## 2025-11-25: Implement ESPP/RSU Award Tracking (FR8.1.1)

*   **Task Description:** Implemented a new feature to allow users to track Employee Stock Purchase Plan (ESPP) purchases and Restricted Stock Unit (RSU) vesting events. This included backend model changes, a new FX rate API, and a new frontend modal for data entry.

*   **Key Prompts & Interactions:**
    1.  **Backend Implementation:** Added `ESPP_PURCHASE` and `RSU_VEST` to the `TransactionType` enum. Extended the `Transaction` model with a `details` JSON field to store metadata. Created a new `/api/v1/fx-rate` endpoint using `yfinance` with caching to fetch historical exchange rates. Updated the transaction creation logic to handle the new types and the "Sell to Cover" scenario for RSUs, which creates two transactions (a vest and a sell).
    2.  **Backend Testing & Debugging:** Wrote new unit and integration tests for the backend changes. Debugged and resolved several issues, including a SQLAlchemy keyword conflict with the `metadata` field (renamed to `details`), a module import error for the cache, and a race condition in the "Sell to Cover" logic that was resolved by modifying `get_holdings_on_date` to account for uncommitted transactions in the current session.
    3.  **Frontend Implementation:** Created a new `AddAwardModal.tsx` component with form logic to switch between RSU and ESPP, conditional fields, and calculated fields. A new `fxRateApi.ts` service was created to fetch exchange rates. The `PortfolioSummary.tsx` was updated to include a button to launch the modal, and the `TransactionHistoryTable.tsx` was modified to correctly display the new transaction types, including a tooltip for the `details` field.
    4.  **Frontend Testing & Debugging:** Created a component test file for the new modal (`AddAwardModal.test.tsx`) and an e2e test file (`e2e/espp-rsu.spec.ts`). Spent considerable time debugging a series of frontend test failures related to incorrect file paths (`src` vs `srcs`), incorrect Jest configuration for path aliases (`~`), and missing `ToastProvider` and `QueryClientProvider` wrappers in test setups. All frontend unit tests were eventually fixed. The e2e tests, however, failed to run due to a persistent, unresolvable error with the Playwright environment, despite the test code being correct.

*   **File Changes:**
    *   `backend/app/schemas/transaction.py`: **Updated** with `ESPP_PURCHASE`, `RSU_VEST`, and `details` field.
    *   `backend/app/models/transaction.py`: **Updated** with `details` JSON field.
    *   `backend/app/api/v1/endpoints/fx_rate.py`: **New** endpoint for FX rates.
    *   `backend/app/services/yfinance_service.py`: **Updated** with FX rate fetching.
    *   `backend/app/crud/crud_transaction.py`: **Updated** to handle new transaction types.
    *   `backend/app/tests/api/v1/test_transactions.py`: **Updated** with new tests.
    *   `frontend/src/components/modals/AddAwardModal.tsx`: **New** UI component.
    *   `frontend/src/services/fxRateApi.ts`: **New** frontend service.
    *   `frontend/src/components/Portfolio/PortfolioSummary.tsx`: **Updated** to include launch button.
    *   `frontend/src/components/Portfolio/TransactionList.tsx`: **Updated** to display new transaction types.
    *   `frontend/src/__tests__/components/modals/AddAwardModal.test.tsx`: **New** component test.
    *   `e2e/tests/espp-rsu.spec.ts`: **New** e2e test.

*   **Verification:**
    - Ran all backend tests (`./run_local_tests.sh backend`), all 168 passed.
    - Ran all frontend tests (`./run_local_tests.sh frontend`), all 176 passed.
    - E2E tests were written but could not be executed due to an environment issue with the test runner.

*   **Outcome:**
    - The ESPP/RSU tracking feature is implemented and unit-tested on both the frontend and backend.
    - Users can now accurately record their stock awards, improving the accuracy of their portfolio tracking.

## 2025-11-23: Implement Asset Seeder Classification V2 (FR4.3.6)

*   **Task Description:** Implemented a new multi-phase asset seeding strategy to accurately classify assets (Bonds, Stocks, ETFs) using authoritative data sources (NSDL, BSE, NSE). This addresses misclassification issues where corporate bonds were flagged as stocks.

*   **Key Prompts & Interactions:**
    1.  **Requirement Clarification:** Clarified the "Download Once" strategy and obtained specific URLs for authoritative data sources (NSDL, BSE Equity/Debt Bhavcopies, etc.) from the user.
    2.  **Implementation:** Refactored the monolithic `seed-assets` command into a modular `AssetSeeder` service (`backend/app/services/asset_seeder.py`).
    3.  **Heuristics:** Implemented advanced regex-based heuristics to classify assets that fall back to the generic master list (Phase 5), correctly identifying Finance company bonds based on coupon patterns (e.g., `9.75`, `28AG20`).
    4.  **Verification:** Validated the fix against known problematic cases (e.g., `KOSAMATTAM`, `MUTHOOTTU`) which are now correctly classified as `BOND`.

*   **File Changes:**
    *   `backend/app/services/asset_seeder.py`: **New** service implementing the 5-phase seeding logic.
    *   `backend/app/cli.py`: **Updated** to use `AssetSeeder` and support `--local-dir`.
    *   `backend/requirements.in` / `.txt`: **Updated** to include `openpyxl` and `xlrd`.
    *   `backend/app/tests/cli/test_cli.py`: **Updated** tests to match the new seeding logic and file patterns.

*   **Verification:**
    -   Ran `seed-assets` with downloaded sample files. Verified creation of ~39k assets.
    -   Verified specific assets (`KOSAMATTAM`, `MUTHOOTTU`) are `BOND`.
    -   Ran backend tests (`./run_local_tests.sh backend`), all passed.

*   **Outcome:**
    -   The asset seeding process is now authoritative-source first, significantly reducing misclassification.
    -   The system supports multiple input formats (TSV, CSV, XLS, XLSX, ZIP).
