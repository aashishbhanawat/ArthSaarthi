# Personal Portfolio Management System (PMS) - Requirements

This document outlines the functional and non-functional requirements for the PMS application.

## 1. Core Principles

-   **CP1: Strict Data Privacy.** The system must enforce strict data segregation. No user, including those with an `admin` role, shall be able to view or access another user's personal financial information (portfolios, transactions, assets, etc.).

## 2. Functional Requirements

### FR1: Core User Management & Authentication

-   **FR1.1: Initial Setup Check.** On application startup, the system must check if any user accounts exist.
-   **FR1.2: Initial Admin Setup.** If no users exist, the user must be directed to an "Initial Setup" page to create the first user account (username, email, password).
-   **FR1.3: Admin Role Assignment.** The first user created must be automatically assigned the `admin` role. All subsequent users created by an admin will have the `user` role.
-   **FR1.4: Secure Login.** All users must be able to log in securely.
-   **FR1.5: Profile Management.** All users must have a dedicated profile/settings page to manage their account.
    -   **FR1.5.1:** Users must be able to update their non-critical profile information (e.g., full name).
    -   **FR1.5.2:** Users must be able to change their password. This action should require them to enter their current password for verification.
    -   **FR1.5.3:** Users must be able to change their login email. This action must trigger a verification process for the new email address before it becomes active.
-   **FR1.6: Forgotten Password Reset.** Any user must be able to reset their forgotten password.
-   **FR1.7: Secure Logout.** All users must be able to log out.

### FR2: Administration

-   **FR2.1: User Management Dashboard.** An `admin` must have access to a dashboard to view, create, and delete `user` accounts.
-   **FR2.2: Audit Logging Engine.** The system must log security-sensitive events (e.g., login success/failure, user creation/deletion, data import/export). Logs must include Geo/IP tagging.
-   **FR2.3: Log Viewing.** An `admin` must be able to view these audit logs.

### FR3: Portfolio Dashboard

-   **FR3.1:** Upon login, users see a consolidated dashboard summarizing all their portfolios and investments.
-   **FR3.2:** The dashboard must display the total aggregated value of all investments.
-   **FR3.3:** It should show the overall profit/loss, as well as the percentage change for different timeframes (daily, weekly, overall).
-   **FR3.4:** The dashboard must feature a "Privacy Mode" toggle that hides/unhides all monetary amounts across the application.
-   **FR3.5:** The dashboard must provide a breakdown of investments by individual asset holdings and by asset class.
-   **FR3.6:** An interactive pie chart must visualize the asset allocation by asset class.
-   **FR3.7:** An interactive line chart must display the historical value of the user's total investments over time.

### FR4: Portfolio, Asset & Transaction Management
-   **FR4.1: Portfolio Management.** Users must be able to create, name, and manage multiple goal-based portfolios (e.g., "Retirement", "Child's Education"). Users can also group portfolios to view consolidated holdings.
-   **FR4.2: Asset Association.** When adding a market-traded asset (Stock, ETF, Mutual Fund), the user must associate it with one of their created portfolios. Other asset types (like FDs, PPF) can be tracked at the top level, outside of specific portfolios.
-   **FR4.3: Asset Support.** The system must support tracking a wide variety of asset types:
    -   **Market-Traded:** Stocks, ETFs, Mutual Funds, Bonds.
    -   **Employee Plans:** Restricted Stock Units (RSUs) and Employee Stock Purchase Plans (ESPPs), accommodating both Indian and US variants and their respective currencies (e.g., INR, USD).
    -   **Fixed Income & Savings:** Fixed Deposits (FDs), Recurring Deposits (RDs), Public Provident Fund (PPF), National Pension System (NPS).
-   **FR4.4: Transaction Management.**
    -   **FR4.4.1:** Users must be able to manually add, edit, and delete assets and their transactions.
    -   **FR4.4.2:** Transaction details must include: type (buy/sell), symbol/ticker, quantity, price, date, currency, and any associated fees.
-   **FR4.5: Income Tracking.** The system must track dividends, interest payments, and other distributions, with an option to mark them as reinvested.
-   **FR4.6: Corporate Actions.** The system must automatically track and apply corporate actions like dividends, bonuses, splits, mergers, and demergers for stocks in portfolios.
-   **FR4.7: Portfolio Detail Page View (Pilot Feedback).** The portfolio detail page must be redesigned to provide a consolidated, analytical view.
    -   **FR4.7.1: Portfolio Summary Header.** The top of the page must display a summary card with key metrics for that portfolio: Total Value, Invested Amount, Day's P&L (Absolute & %), Unrealized P&L (Absolute & %), and Realized P&L.
    -   **FR4.7.2: Consolidated Holdings View.** The primary view must be a table of consolidated current holdings, replacing the raw transaction list. Each row must represent a single asset and display: Asset Name, Quantity, Average Buy Price, Invested Amount, LTP, Day's Change (%), Day's P&L, Current Value, and Unrealized P&L (Absolute & %).
    -   **FR4.7.3: Holdings Drill-Down View.** Clicking on a holding row must reveal a detailed view for that specific asset.
        -   **FR4.7.3.1: Asset Summary.** The drill-down must show a summary for the asset, including ISIN, current price, and on-demand calculation buttons for XIRR.
        -   **FR4.7.3.2: Buy Transaction History.** The drill-down must list all *buy* transactions that constitute the current holding. Each transaction row must include: Buy Date, Quantity, Buy Price, Fees, Invested Amount, Overall Gain (%), Current Value, and CAGR %.
        -   **FR4.7.3.3: Transaction Actions.** Each transaction row in the drill-down view must provide options to Edit or Delete the transaction. This links to requirement **FR4.4.1**.
-   **FR4.8: Dedicated Transaction History Page (Pilot Feedback).**
    -   **FR4.8.1:** A separate, dedicated page must be created to display the full, raw transaction list for a portfolio.
    -   **FR4.8.2:** By default, this page must only show transactions for the current financial year.
    -   **FR4.8.3:** The page must include filters to view historical transactions by date range, transaction type, and asset.

### FR5: Data Integration & Real-time Updates

-   **FR5.1:** The system must integrate with a third-party financial data API to fetch market prices.
-   **FR5.2: Price Updates.**
    -   **FR5.2.1:** Provide live price updates for Stocks and ETFs (e.g., with a 15-minute delay).
    -   **FR5.2.2:** Provide daily NAV updates for Mutual Funds and daily price updates for Listed Bonds.

-   **FR6.1: Performance Metrics.** The system must calculate and display:
    -   Absolute Gain/Loss (Realized and Unrealized).
    -   Annualised Return (XIRR) for any asset, asset class, portfolio, or group.
    -   Time-weighted Return (TWR) and Money-weighted Return (MWR).
-   **FR6.2: Advanced Risk Analytics.** The system must calculate and display risk and performance metrics including:
    -   Volatility (Standard Deviation), Sharpe Ratio, Beta, Alpha, Tracking Error, and Maximum Drawdown.
-   **FR6.3: Benchmarking.** Users must be able to compare their portfolio's performance against standard market benchmarks (e.g., Nifty 50, S&P 500) over a rolling 12-month period.
-   **FR6.4: Diversification Analysis.** Provide visual breakdowns of the portfolio by: Asset Class, Industry/Sector, Geography, Currency, Market Cap, and Investment Style (Growth vs. Value).
-   **FR6.5: Capital Gains Reporting.**
    -   **FR6.5.1:** Generate reports for realized long-term, short-term, and intra-day capital gains in ITR (Income Tax Return) format.
    -   **FR6.5.2:** Reports must account for provisions like LTCG Grandfathering and Indexation.
    -   **FR6.5.3:** Users must be able to view unrealised capital gains to estimate tax liability.
-   **FR6.6: Customizable Reports.**
    -   **FR6.6.1:** Users must be able to generate and export reports in PDF/CSV format.
    -   **FR6.6.2:** Available reports include: Income, Due Dates, Transactions, Holding Period, and Asset Allocation.
-   **FR6.7: Historical Data.** The system must maintain and display historical end-of-month valuations for Stock and MF portfolios.

### FR7: Data Import
-   **FR7.1: Automated Import.** The system must support direct import of statements to automate transaction logging.
    -   **FR7.1.1:** Stock/F&O contract notes from brokers like Zerodha and ICICI Direct.
    -   **FR7.1.2:** Mutual Fund CAS statements from CAMSOnline or NSDL.
    -   **FR7.1.3:** eNPS statements from Karvy or NSDL.
    -   **FR7.1.4:** PMS & AIF statements.
-   **FR7.2: File Format Support.** The import engine must handle various file formats, including PDF, Excel, HTML, CSV, TXT, and DBF.

### FR8: Market Insights & Research
-   **FR8.1: Watchlists.** Users must be able to create and manage lists of assets to monitor without owning them, displaying key metrics for each.
-   **FR8.2: Market News Feed.** The system will provide an aggregated feed of financial news relevant to the user's portfolio and watchlist.
-   **FR8.3: Asset Detail Pages.** A detailed view for individual assets must be available, showing historical price charts, key financial metrics (Market Cap, Volume, P/E), company descriptions, and related news.

### FR9: Notifications & Alerts
-   **FR9.1: User-defined Alerts.** Users can set price alerts (e.g., notify if an asset goes above/below a threshold) and receive news alerts.
-   **FR9.2: Due Date Reminders.** The system will provide notifications for upcoming due dates for FDs, NPS contributions, or other renewals.
-   **FR9.3: Delivery Channels.** Notifications will be delivered via a push notification service and/or a Telegram bot.

### FR10: AI-Powered Insights
-   **FR10.1: Configurable AI Engine.** Users can connect to external AI APIs (e.g., Gemini, OpenAI) to generate insights.
-   **FR10.2: Tax-Saving Suggestions.** The AI will suggest tax-loss harvesting opportunities based on unrealized gains/losses and provide automatic year-wise export options.
-   **FR10.3: Risk & Rebalancing.** The AI will provide insights on asset correlation for risk management and suggest rebalancing actions based on volatility or dynamic goals.
-   **FR10.4: SIP Optimization.** The AI can suggest optimal SIP dates based on user-defined cash flow timing.

### FR11: User Experience
-   **FR11.1: Theming.** The application must support Light and Dark mode themes.
-   **FR11.2: Internationalization (i18n).** The application should be designed to support multiple languages in the future.

### FR12: Risk Profile Management
-   **FR12.1: Risk Profile Questionnaire.** The system must provide a questionnaire for users to assess their risk tolerance, risk capacity, investment horizon, and financial goals.
-   **FR12.2: Risk Score Calculation.** Based on the questionnaire responses, the system must calculate a risk score and assign the user to a clear risk category (e.g., Conservative, Moderate, Aggressive).
-   **FR12.3: Portfolio Risk Assessment.** The system must calculate the overall risk level of the user's current portfolio based on its asset composition and predefined risk factors for each asset class.
-   **FR12.4: Risk Alignment Dashboard.** A dedicated page or dashboard section must:
    -   Display the user's determined risk profile (e.g., "Your Profile: Moderate").
    -   Display the calculated risk level of their current portfolio (e.g., "Your Portfolio's Risk: Aggressive").
    -   Clearly indicate if there is a mismatch between the user's profile and their portfolio's risk.
-   **FR12.5: Rebalancing Suggestions (Advanced).** The system should offer suggested rebalancing actions or show model portfolios that align with the user's determined risk profile.

### FR13: Advanced Goal Planning & Tracking (New Section)
-   **FR13.1: Goal Definition.** Users must be able to define specific financial goals with a name, target amount, and target date.
-   **FR13.2: Asset Linking.** Users must be able to link entire portfolios or individual assets to one or more defined goals.
-   **FR13.3: Contribution Planning.** The system should calculate the required contribution rate (e.g., monthly) needed to achieve a goal.
-   **FR13.4: Projection & Analysis.** The system must project the future value of linked assets and determine if the user is on track to meet their goal.
-   **FR13.5: Goal Dashboard.** Each goal must have a visual dashboard showing progress, projection charts, and on/off-track status.

### FR14: Future Scope (Renumbered)
-   **FR14.1: Two-Factor Authentication (2FA).**
-   **FR14.2: Companion Mobile App.**

## 3. Non-Functional Requirements

-   **NFR1: Security:** Use HTTPS, hash passwords, secure APIs (JWT), and protect against common vulnerabilities.
-   **NFR2: Performance:** API responses < 500ms, page loads < 3s, cache third-party API calls.
-   **NFR3: Usability:** The UI must be clean, modern, intuitive, and optimized for desktop, tablet, and mobile web browsers.
-   **NFR4: Scalability:** Architecture must handle user growth.
-   **NFR5: Reliability & Data Integrity:** Accurate calculations, high uptime, regular backups.
-   **NFR6: Deployment:** The application must be deployable in a Docker environment, specifically on a Raspberry Pi, and accessible via a Cloudflare tunnel.
-   **NFR7: Data Management:** The system must provide a mechanism for users to back up and restore their portfolio data.
