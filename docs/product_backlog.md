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

The goal of this release is to broaden the asset types supported and introduce more powerful analytics and data import features.

**Features:**

-   **Advanced Asset Support (FR4):** Add support for FDs, RDs, PPF, NPS, Bonds, RSUs, ESPPs.
-   **Automated Data Import (FR7):** Implement file parsers for broker statements (Zerodha, ICICI) and MF CAS.
    -   **Status: ✅ Backend Complete**
-   **Advanced Reporting & Analytics (FR6):**
    -   Implement XIRR and Sharpe Ratio for portfolios.
    -   **Status: ✅ Complete**
-   **Risk Profile Management (FR12):** Implement the risk questionnaire and portfolio alignment dashboard.
-   **Goal Planning & Tracking (FR13):** Implement the goal definition and progress tracking module.

## Future Releases

-   **Market Insights & Research (FR8):** Watchlists, news feeds.
-   **Notifications & Alerts (FR9):** Price alerts, due date reminders via Telegram/Push.
-   **AI-Powered Insights (FR10):** Tax-saving suggestions, risk analysis.
-   **Advanced UX (FR11):** Theming, internationalization.
-   **Two-Factor Authentication (FR14.1)**
-   **Companion Mobile App (FR14.2)**