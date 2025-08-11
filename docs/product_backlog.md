# Product Backlog & Development Roadmap

This document outlines the prioritized list of features for the Personal Portfolio Management System (PMS). We will follow an iterative development approach, starting with a Minimum Viable Product (MVP).

## Release 1: Minimum Viable Product (MVP)

**Status: ✅ COMPLETE (as of 2025-07-27)**

The goal of the MVP was to deliver a functional core product that allows a user to set up an account, create a portfolio, manually add common assets, and track their value. All planned features are now implemented and stable.

**Features:**

1.  **Core User Authentication (FR1):**
    -   Initial admin setup if no users exist.
    -   Standard user login.
    -   Secure JWT-based authentication.
    -   **Status: ✅ Complete**

2.  **Basic Administration (FR2):**
    -   Admin can create and delete standard users from a simple dashboard.
    -   **Status: ✅ Complete**

3.  **Portfolio & Transaction Management (Core from FR4):**
    -   Users can create, edit, and delete multiple, named portfolios.
    -   Users can manually add, edit, and delete transactions for **Stocks, ETFs, and Mutual Funds** within a portfolio.
    -   Support for different currencies on transactions.
    -   **Status: ✅ Complete**

4.  **Dashboard (Core from FR3):**
    -   Consolidated view of total portfolio value.
    -   Overall Profit/Loss calculation.
    -   Asset allocation pie chart.
    -   Historical value line chart.
    -   Top daily market movers table.
    -   **Status: ✅ Complete**

5.  **Data Integration (FR5):**
    -   Integrate with a third-party financial data API to fetch current market prices for tracked assets.
    -   **Status: ✅ Complete**

## Release 2: Advanced Asset Management & Analytics

**Status: 🚧 In Progress**

The goal of this release is to act on the critical feedback from the pilot release, focusing on core usability enhancements and a major redesign of the portfolio detail page to better meet user needs.

**Features:**

-   **Edit/Delete Transactions (FR4.4.1):** Implement the ability for users to edit and delete their existing transactions.
    -   **Status: ✅ Complete**

-   **Portfolio Page Redesign (FR4 Enhancement):** A complete overhaul of the portfolio detail page based on user feedback.
    -   **Portfolio Summary:** Display key metrics (Total Value, P&L, etc.) at the top of the page.
    -   **Consolidated Holdings View:** Replace the transaction list with a consolidated view of current holdings, showing quantity, average price, current value, and P&L for each stock.
    -   **Transaction Drill-Down:** Allow users to click on a holding to see its detailed transaction history.
    -   **Status: 🚧 In Progress**

-   **Dedicated Transaction History Page (FR4 Enhancement):** Move the full transaction list to a separate, filterable page.
    -   **Status: 📝 Planned**

-   **Advanced Reporting & Analytics (FR6):**
    -   Implement XIRR and Sharpe Ratio for portfolios.
    -   **Status: ✅ Complete**

-   **Context-Sensitive User Guide (FR11 Enhancement):** Make the user guide accessible from within the application via context-sensitive help icons.
    -   **Status: ✅ Complete**

## Release 3: Automated Data Import

**Status: ✅ COMPLETE (as of 2025-08-11)**

The goal of this release was to build a robust and user-friendly system for importing transaction data from external brokerage statements, reducing manual data entry.

**Features:**

-   **Automated Data Import - Phase 2 (FR7):**
    -   Implement a two-stage import workflow (upload/preview/commit).
    -   Implement a parser strategy pattern to handle different file formats.
    -   Create specific parsers for Zerodha and ICICI Direct tradebooks.
    -   Redesign the frontend to support a categorized preview and selective committing of transactions.
    -   Add logic to sort transactions by date/ticker/type to ensure data integrity.
    -   **Status: ✅ Complete**

## Future Releases

-   **Automated Data Import - Phase 3 (FR7):** Implement a parser for Consolidated Account Statements (MF CAS) to support mutual fund transaction imports.
-   **Advanced Asset Support (FR4):** Add support for FDs, RDs, PPF, NPS, Bonds, RSUs, ESPPs.
-   **Risk Profile Management (FR12):** Implement the risk questionnaire and portfolio alignment dashboard.
-   **Goal Planning & Tracking (FR13):** Implement the goal definition and progress tracking module.
-   **Market Insights & Research (FR8):** Watchlists, news feeds.
-   **Notifications & Alerts (FR9):** Price alerts, due date reminders via Telegram/Push.
-   **AI-Powered Insights (FR10):** Tax-saving suggestions, risk analysis.
-   **Advanced UX (FR11):** Theming, internationalization.
-   **Two-Factor Authentication (FR14.1)**
-   **Companion Mobile App (FR14.2)**