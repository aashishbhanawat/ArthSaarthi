**Feature ID:** TST-E2E-ANL-01
**Title:** E2E Test for Asset-Level XIRR Analytics
**User Story:** As a developer, I want an end-to-end test that verifies the asset-level XIRR calculations are correctly displayed in the UI, so that I can prevent regressions in this feature.

## 1. Functional Requirements

- The test will create a new portfolio.
- The test will create a new asset with a specific ticker (`XIRRTEST`).
- The test will add a BUY transaction for this asset with a date exactly one year in the past.
- The test will add a SELL transaction for a partial quantity of this asset with a date exactly six months in the past.
- The test will navigate to the portfolio detail page and open the "Holdings Drill-Down" modal for the asset.
- The test will wait for the analytics data to load.
- The test will assert that the "Realized XIRR" and "Unrealized XIRR" values are displayed and match the expected calculated percentages.

## 2. Technical Design

1.  **Backend:**
    -   Add mock price data for the `XIRRTEST` ticker to the `FinancialDataService` to ensure the test is deterministic.
2.  **E2E Test Suite:**
    -   Create a new test file `e2e/tests/analytics.spec.ts`.
    -   The test will perform the steps outlined in the functional requirements.
    -   Assertions will check for the text `43.86%` (Realized XIRR) and `30.00%` (Unrealized XIRR) within the modal.

