feat: Complete pilot release with P/L, Top Movers, and Asset Creation

This commit marks the completion of the pilot release. It includes the implementation of several key features and a comprehensive stabilization pass that resolved numerous bugs found during end-to-end testing.

Key Features Implemented:
-   **Profit & Loss Calculation:** Implemented backend logic for realized and unrealized P/L using the Average Cost Basis method.
-   **Top Movers:** Added a "Top Movers" table to the dashboard with backend logic to calculate daily price changes.
-   **On-the-fly Asset Creation:** Implemented a new user flow allowing users to add assets not present in the pre-seeded database.
-   **Sliding Sessions:** Implemented a refresh token authentication system to provide a better user experience.

Stabilization & Bug Fixes:
-   Resolved numerous UI bugs related to currency formatting, modal rendering, and component styling.
-   Fixed backend data integrity issues, including transaction validation and historical data calculation.
-   Stabilized the entire frontend and backend test suites.
-   Updated all project documentation to reflect the current state of the application.

Bug Fixes:
-   Resolves all outstanding bugs documented up to 2025-07-27.

All backend and frontend tests are passing. The application is stable and all MVP features are complete.