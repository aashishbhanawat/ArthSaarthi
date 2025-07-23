feat: Complete MVP and stabilize application

This commit marks the completion of the Minimum Viable Product (MVP). It includes the final implementation of the dashboard visualization charts and a comprehensive stabilization pass that resolved numerous bugs found during end-to-end testing.

Key Changes:
-   **Backend Validation:** Added critical validation to the transaction creation logic to prevent selling assets before they are owned.
-   **Frontend Error Handling:** Refactored the "Add Transaction" modal to display specific, user-friendly error messages from the backend API.
-   **Code Quality:** Refactored the frontend transaction creation flow for better maintainability and type safety.
-   **Test Coverage:** Added a new backend test suite to cover the new transaction validation logic.
-   **Bug Fixes:** Resolved multiple bugs related to mock data, API logic, and UI styling that were discovered during E2E testing.

Bug Fixes:
-   Resolves bugs 2025-07-23-09 through 2025-07-23-19.

All backend and frontend tests are passing. The application is stable and all MVP features are complete.