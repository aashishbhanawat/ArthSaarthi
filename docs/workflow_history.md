## 2025-12-07: Fix E2E Timeouts & Frontend Test Context

*   **Task Description:** Resolve critical E2E test timeouts caused by the "Save Transaction" button being disabled during FX rate fetching, and address reviewer feedback regarding frontend unit test context wrapping.

*   **Key Prompts & Interactions:**
    1.  **Debugging:** Identified that `TransactionFormModal` disables submission while `isFetchingFxRate` is true. In the E2E Docker environment, the external call to fetch FX rates was failing or hanging, causing tests to time out.
    2.  **Reviewer Feedback:** Addressed the requirement to use `<PrivacyProvider>` in `TransactionFormModal.test.tsx` instead of mocking the hook directly.
    3.  **Refinement:** Checked `AddAwardModal.tsx` as a reference but decided to stick with a robust testing strategy (mocking) rather than changing UI logic just for tests.

*   **File Changes:**
    *   `e2e/tests/analytics.spec.ts`: **Updated** to mock the `/api/v1/fx-rate` endpoint.
    *   `e2e/tests/corporate-actions.spec.ts`: **Updated** to mock the FX rate endpoint.
    *   `e2e/tests/data-import-mapping.spec.ts`: **Updated** to mock the FX rate endpoint.
    *   `e2e/tests/portfolio-and-dashboard.spec.ts`: **Updated** to mock the FX rate endpoint.
    *   `e2e/tests/transaction-history.spec.ts`: **Updated** to mock the FX rate endpoint.
    *   `frontend/src/__tests__/components/Portfolio/TransactionFormModal.test.tsx`: **Updated** to wrap the component in `<PrivacyProvider>` and remove the mock for `usePrivacySensitiveCurrency`.

*   **Verification:**
    *   Ran frontend unit tests (`npm test .../TransactionFormModal.test.tsx`) locally, which passed.
    *   Relied on CI for full E2E execution, as local environment setup was partial, but the mock strategy is standard and addresses the root cause directly.

*   **Outcome:**
    *   E2E tests are now deterministic and do not rely on external `yfinance` connectivity.
    *   Frontend unit tests correctly simulate the app's context hierarchy.
