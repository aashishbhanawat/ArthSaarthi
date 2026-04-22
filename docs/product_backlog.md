# Product Backlog & Development Roadmap

This document outlines the prioritized list of features for **ArthSaarthi**, a personal portfolio management system. We will follow an iterative development approach, starting with a Minimum Viable Product (MVP).

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
    -   **Holdings Table Redesign:** Redesign the holdings table to group assets by class into collapsible sections.
    -   **Status: ✅ Complete**

-   **Advanced Reporting & Analytics (FR6):**
    -   Implement XIRR and Sharpe Ratio for portfolios.
    -   **Benchmarking (FR6.3):** Compare portfolio performance against Nifty 50 and Sensex.
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

## Release 4: Advanced Transaction Filtering

**Status: ✅ COMPLETE (as of 2025-08-22)**

-   **Dedicated Transaction History Page (FR4.8):** Move the full transaction list to a separate, filterable page with filters for date range, type, and asset.
    -   **Status: ✅ Complete**

## Release 5: Goal Management & Insights

**Status: ⚠️ Partially Implemented**

**Features:**

-   **Watchlists (FR8.1):** Users can create, manage, and track custom lists of financial assets.
    -   **Status: ✅ Complete**
-   **Goal Planning & Tracking (FR13):** Implement core goal definition, asset linking, and basic progress tracking. **Status: ⚠️ Partially Implemented**
-   **Mutual Fund Dividend Tracking (FR4.5.1):** Add support for logging cash and reinvested dividends for mutual funds.
    -   **Status: ✅ Complete**

## Release 6: Security & Administration

**Status: ✅ COMPLETE (as of 2025-08-26)**

**Features:**

-   **Audit Logging Engine (FR2.2):** A backend engine to securely log all sensitive user and system events.
    -   **Status: ✅ Complete**

## Release 7: User Experience & Security

**Status: ✅ COMPLETE (as of 2025-08-30)**

**Features:**

-   **User Profile Management (FR1.5):** Implement user profile settings page for name and password changes.
    -   **Status: ✅ Complete**

-   **Inactivity Timeout (FR1.8):** Automatically log out users after a period of inactivity.
    -   **Status: ✅ Complete**

## Release 8: User Experience Enhancements

**Status: ✅ COMPLETE (as of 2025-09-03)**

**Features:**

-   **Privacy Mode (FR3.4):** Add a "Privacy Mode" toggle to the dashboard to obscure sensitive financial data.
    -   **Status: ✅ Complete**

## Release 9: Advanced Asset Support

**Status: ✅ COMPLETE (as of 2025-12-05)**

**Features:**

-   **Advanced Asset Support (FR4):**
    -   Fixed Deposits (FDs): **✅ Complete**
    -   Recurring Deposits (RDs): **✅ Complete**
    -   Public Provident Fund (PPF): **✅ Complete**
    -   Bonds (Corporate, Govt, SGB, T-Bill): **✅ Complete**
    -   Asset Seeder Classification V2 (FR4.3.6): **✅ Complete**
    -   ESPP/RSU Tracking (FR4.3): **✅ Complete**

## Release 10: Global Markets & Currency

**Status: ✅ COMPLETE (as of 2025-12-11)**

**Features:**

-   **Foreign Stock & Currency Support (FR4.3):** Track assets in foreign currencies (e.g., USD) with automatic INR consolidation using historical FX rates.
    -   **Status: ✅ Complete**
-   **Foreign Income Tracking (FR4.6.1):** Correctly handle dividends and coupons for foreign assets using historical FX rates.
    -   **Status: ✅ Complete**

## Release 11: Tax Optimization & Accounting

**Status: ✅ COMPLETE (as of 2025-12-15)**

**Features:**

-   **Tax Lot Accounting (FR4.4.3):** Implement "Specific Lot Identification" for sales to optimize tax liability, with FIFO fallback.
    -   **Status: ✅ Complete**
-   **Stock Dividend Reinvestment (DRIP) (FR4.6.1):** Support for automatic reinvestment of stock dividends.
    -   **Status: ✅ Complete**

## Release 12: Next Steps & Maintenance

**Status: ✅ COMPLETE (as of 2026-03-24)**

**Features:**

-   **Manual Asset Seeding (FR9):** Allow admins to trigger asset master updates from the UI without restarting the server.
-   **Capital Gains Report (FR10):** Generate Short-Term (STCG), Long-Term (LTCG), and Schedule 112A reports. **✅ Complete**
-   **Foreign Assets Reporting (Schedule FA):** Peak Value tracking and Calendar Year reporting. **✅ Complete**
-   **Symbol Alias Management (#215):** Admin UI to view, create, edit, and delete symbol aliases used during data import. **✅ Complete**
-   **ICICI ShortName Alias Seeding (#216):** Auto-create ICICI ShortName → Ticker aliases during asset seeding for seamless tradebook imports. **✅ Complete**
-   **ICICI Portfolio Import (#217):** Support for importing ICICI Direct Portfolio Equity history files (TSV/XLS). **✅ Complete**
-   **Daily Portfolio Snapshots (#162):** Cache daily valuations for history chart. **✅ Complete**
-   **Advanced Benchmarking (FR6.3):** Hybrid benchmarks, risk-free rate overlay, and category-level (equity/debt) XIRR comparison. **✅ Complete**
-   **Portfolio Delete FK Error Handling:** 409 Conflict response for portfolios linked to goals, with frontend error display. **✅ Complete**
-   **Non-Market Asset Historical Chart Accuracy:** Fixed FD/RD/PPF/Bond historical values in portfolio chart. **✅ Complete (edge cases may remain)**
-   **Fixed Deposit Import from Bank Statements (FR7.2.1):** Import FDs from HDFC, ICICI, and SBI combined PDFs. **✅ Complete**
-   **Test Coverage Audit (#250):** Review all backend integration tests to identify gaps in coverage, particularly for RSU/ESPP/foreign asset holdings calculations, linked transaction sell paths, and edge cases in analytics (XIRR, P&L). Prompted by Issue #249 where missing test coverage allowed a bug in RSU avg price calculation to go undetected.
-   **Automated Data Import - Phase 3 (FR7):** Implement a parser for Consolidated Account Statements (MF CAS).

## Detailed Future Release Plan

### Release v1.3.0: Context & Risk Foundations
**Focus: Establishing user intent and risk boundaries before AI integration.**
-   **Risk Profile Management (FR12):**
    -   Risk Profile Questionnaire to determine risk tolerance (Conservative, Moderate, Aggressive).
    -   Portfolio Risk Assessment (calculating current allocation risk).
    -   Risk Alignment Dashboard to flag mismatches.
-   **Goal Projections & Analytics (FR13 Phase 2):**
    -   Calculate required contribution rates (SIPs) to hit goal targets.
    -   Project future value of linked assets using current XIRR to determine "On-Track" status.

### Release v1.4.0: Tax Readiness & Full Financial Picture
**Focus: Providing the system with all tax-related context necessary for future AI tax-saving recommendations.**
-   **Unrealized Capital Gains (FR6.5 Phase 2):**
    -   Calculate and display unrealized STCG/LTCG for active holdings.
    -   Implement precise exemption pooling (e.g., ₹1.25L equity LTCG exemption).
-   **Income & Tax Data Management (FR16):**
    -   Log income sources (Salary, Freelance, TDS).
    -   Log tax-deductible expenses (Section 80C, Medical).

### Release v1.5.0: Infrastructure, Data & Automation
**Focus: Integrating official data sources, enabling background processing, and improving automation.**
-   **Broker API Integration (NFR12):** Implement pluggable data providers for Zerodha Kite and ICICI Breeze to replace `yfinance`, especially for the Android build. This includes the necessary UI for the daily OAuth user login flow.
-   **API Rate Limiting & Caching (NFR13):** Implement robust caching, request batching, and rate limiting for the new broker APIs to ensure compliance and performance.
-   **Desktop Update Notification (FR-Desktop-2):** Check GitHub Releases API and notify users of new versions.
-   **Background Job Scheduler:** Architectural implementation (e.g., APScheduler) to handle asynchronous tasks.
-   **Automated Corporate Actions:** Use the new scheduler for auto-generation of bond coupons and maturity transactions.
-   **Market News Feed (FR8.2):** Use the new scheduler for background fetching and linking of relevant financial news to user holdings.

### Release v1.6.0: Security, Admin & Advanced UX
**Focus: Polishing core user experience and security before introducing AI.**
-   **Forgotten Password Flow (FR1.6):** Implement a secure password reset mechanism with email routing.
-   **Profile Security (FR1.5.3 & FR14.3):** Change login email with verification, sliding window session expiry.
-   **Admin Audit Log Viewer (FR2.4):** UI for admins to view the generated security audit logs.
-   **Asset Detail Pages (FR8.3):** Deep-dive research pages for individual assets showing historical charts, P/E, and company info.

### Release v2.0.0: AI Co-Pilot Foundations (Major Release)
**Focus: Integrating core GenAI for portfolio insights and natural language reporting.**
-   **Configurable AI Engine (FR10.1):** Allow users/admins to connect their preferred AI API keys (Gemini, OpenAI).
-   **AI Portfolio Rebalancing (FR10.3/10.5):** AI suggests concrete buy/sell actions based on the user's Risk Profile (FR12) and Goals (FR13).
-   **AI Daily/Weekly Digest (FR10.6):** Natural language summary of portfolio performance, market movements, and relevant news.

### Release v2.1.0: AI Tax & Cashflow Optimization
**Focus: Advanced programmatic insights for tax efficiency and automated investing.**
-   **AI Tax-Loss Harvesting (FR10.2):** AI scans unrealized gains/losses to suggest optimal sell-offs, cross-referencing with the v1.4.0 tax engine.
-   **AI SIP Optimization (FR10.4):** Suggesting optimal investment dates and amounts based on logged cash flow (FR16).

### Release v2.2.0: AI Expense Management
**Focus: Expanding the platform into day-to-day cashflow and expense tracking.**
-   **AI-Powered Expense Management (FR15):** 
    - Upload bank and credit card PDF statements.
    - AI parsing and automatic expense categorization.

### Release Backlog (v2.X.X and Beyond)
-   **Advanced Analytics & Reporting (FR6 & FR6.6):** Implement TWR, MWR, Beta, Alpha, Tracking Error, Max Drawdown, and Customizable PDF/CSV Reports.
-   **Notifications & Alerts (FR9):** Price alerts, due date reminders, and delivery via Telegram/Push Notifications.
-   **Advanced Security (FR14.1):** Two-Factor Authentication (2FA).
-   **Platform Expansion:** Internationalization (FR11.2) and Companion Mobile App (FR14.2).
-   **Income & Tax Data Management (FR16) - Phase 2:** Generate structured informational tax summary reports.
-   **National Pension System (NPS):** Track NPS Tier 1 and Tier 2 holdings (Postponed pending sample statements).
-   **PMS/AIF Parsers:** Postponed pending sample statements.
