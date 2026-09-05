# ArthSaarthi - Personal Portfolio Management System

[![CI/CD Status](https://github.com/aashishbhanawat/ArthSaarthi/actions/workflows/ci.yml/badge.svg)](https://github.com/aashishbhanawat/ArthSaarthi/actions/workflows/ci.yml)
[![Backend Tests](https://img.shields.io/badge/Backend_Tests-357/360-brightgreen)](#)
[![Frontend Tests](https://img.shields.io/badge/Frontend_Tests-191/191-brightgreen)](#)
[![E2E Tests](https://img.shields.io/badge/E2E_Tests-34/34-brightgreen)](#)

---

**ArthSaarthi** is a self-hostable, privacy-focused application designed to help users manage their personal investment portfolios. It provides a comprehensive suite of tools for tracking assets, analyzing performance, and making informed financial decisions.

The application is designed for flexibility and can be deployed in two ways: as a multi-user **web service** using Docker for self-hosting, or as a simple, single-user **desktop application** that requires no external database, making it accessible to both technical and non-technical users.

The project was developed following a rigorous, AI-assisted Agile SDLC, with a strong emphasis on automated testing, comprehensive documentation, and iterative feature implementation.

<!-- Optional: Add a link to a live demo if you have one -->
<!-- **[Live Demo](https://your-demo-link.com)** -->

## ✨ Core Features

*   **Secure Authentication & Administration:** JWT-based authentication, initial admin setup, a full admin dashboard for user management (CRUD), a backend **Audit Logging Engine** to record all sensitive events, a dedicated **User Profile Page** to manage your account, and an **Inactivity Timeout** to automatically log out users.
*   **Dynamic Dashboard:** Get a bird's-eye view of your financial health with a dashboard showing total portfolio value, realized/unrealized P&L, top daily market movers, and interactive charts for portfolio history and asset allocation.
*   **Advanced Portfolio Analytics:** On-demand calculation of **XIRR (Extended Internal Rate of Return)** and **Sharpe Ratio**. Compare your performance against market benchmarks (**Nifty 50**, **Sensex**) with interactive charts.
*   **Comprehensive Portfolio & Transaction Management:**
    *   Full CRUD functionality for portfolios.
    *   Full CRUD functionality for transactions, including a dedicated, filterable **Transaction History** page and support for logging corporate actions (**Dividends, Stock Splits, Bonus Issues**).
    *   Full CRUD and tracking for **Fixed Deposits (FDs)**, **Recurring Deposits (RDs)**, **Public Provident Fund (PPF)** accounts, and **Bonds** with detailed analytics.
    *   **ESPP/RSU Tracking:** A dedicated workflow to add and edit ESPP/RSU awards, including support for 'Sell to Cover' tax withholding transactions.
    *   **Foreign Stock & Currency Support:** Track assets in foreign currencies (e.g., USD). Portfolio values, analytics, and performance metrics are automatically converted and consolidated into your base currency (INR) using real-time and historical FX rates.
*   **Consolidated Holdings View:** A redesigned portfolio page that shows a consolidated holdings table with sorting, replacing a simple transaction list.
*   **Sectioned Holdings Table:** A redesigned holdings table that groups assets by class into collapsible sections for a clearer overview.
*   **Mutual Fund Dividend Tracking:** Manually log cash or reinvested dividends for mutual fund holdings.
*   **Stock Dividend Reinvestment (DRIP):** Support for automatic reinvestment of stock dividends.
*   **Holdings Drill-Down:** Click on any holding to see a detailed modal with its constituent buy transactions, calculated using FIFO logic.
*   **Automated Data Import:** A full-stack workflow for uploading, parsing, previewing, and committing transaction data from CSV/Excel/PDF files.
    *   Includes pre-built parsers for Zerodha, ICICI Direct (Tradebook & Portfolio), MFCentral CAS, CAMS Statement, Zerodha Coin MF, KFintech PDF, generic format, and **Fixed Deposit (FD) PDFs** (HDFC, ICICI, SBI).
    *   Features an advanced UI for on-the-fly **asset alias mapping** for unrecognized ticker symbols, with admin management (view, edit, delete) of all aliases.
*   **Tax Compliance & Tax Readiness (Release v1.4.0):**
    *   **Schedule FA (Foreign Assets):** Generate reports compliant with Calendar Year rules, including Peak Value analysis (daily balance check) and specific field exports.
    *   **Capital Gains & Loss Set-Off:** Comprehensive reports for Short-Term (STCG) and Long-Term (LTCG) capital gains with statutory intra-head loss set-off rules (Section 70/71/74).
    *   **Unrealized Capital Gains & Exemption Pooling (FR6.5 Phase 2):** Compute lot-level FIFO unrealized STCG/LTCG across active holdings and pool Section 112A LTCG exemption headroom (₹1,25,000 threshold per FY) with interactive tax lot breakdown modals and Privacy Mode currency masking.
    *   **Income Source & Entry Ledger (FR16.1 & FR16.2):** Define income sources (Salary, Freelance, Rental, Dividends, Business) and log entry transactions with gross amount, TDS, net amount, and AES-256 encrypted fields (`EncryptedString`).
    *   **Salary Component Breakdown & Sec 10(13A) HRA Exemption (FR16.5):** Statutory HRA exemption engine computing Basic, DA, HRA, Rent Paid, Metro status, and calculated HRA exemption with 100% mathematical parity against benchmark Excel tax calculators (`local/TaxCalc_2027.xlsx`).
    *   **Tax-Deductible Expense & Investment Logging (FR16.3):** Track Chapter VI-A investments (Sec 80C ₹1.5L, Sec 80D medical insurance, Sec 80CCD(1B) NPS, Sec 80TTA/80TTB interest) with statutory limit progress meters and capping.
    *   **Structured Tax Readiness Summary & Regime Comparison (FR16.4):** Consolidate gross income, TDS credits, eligible deductions, and capital gains to compare tax liability between Old Tax Regime and New Tax Regime (Section 115BAC) with CSV/PDF report exporters and legal non-advisory banners.
    *   **Schedule 112A:** Dedicated support for Grandfathered Equity (acquired before 31 Jan 2018) with FMV lookup and CSV export for ITR-2 filing.
*   **Goal Planning, Projections & Track Status:** Define financial goals (e.g. retirement, buy a car), link portfolios or individual assets, compute dynamic combined XIRR returns, project future value at the target date, determine "On Track" or "Off Track" status, visualize paths via dynamic charts, and calculate required monthly contributions (ordinary annuity SIP) needed to reach your targets.
*   **Market Insights (Watchlists):** Create and manage custom watchlists to monitor assets you don't own.
*   **Flexible Deployment:**
    *   **Server Mode:** A multi-user web service using Docker with PostgreSQL and Redis.
    *   **Desktop Mode:** A single-user, privacy-focused native application using an encrypted SQLite database.
    *   **Android App:** A fully native Capacitor-wrapped Android app running a local Python backend with background WorkManager for daily portfolio snapshots.
*   **Performance:** Expensive analytics and holdings calculations are cached to improve UI responsiveness and reduce server load.

### On the Horizon (Future Features)

*   **Deeper Analytics:** Analyze diversification by sector, geography, and more.
*   **AI-Powered Insights:** Leverage AI to get suggestions for tax-loss harvesting, portfolio rebalancing, and receive a personalized daily digest of your financial world.
*   **Market Insights:** Get relevant news feeds and perform deep-dive research on individual assets.

## 🛠️ Technology Stack

*   **Backend:** Python, FastAPI, SQLAlchemy, Alembic (Migrations)
*   **Frontend:** TypeScript, React, Vite, React Query, Tailwind CSS, Chart.js
*   **Database:** PostgreSQL, SQLite
*   **Caching:** Redis, DiskCache
*   **Testing:** Pytest (Backend), Jest & React Testing Library (Frontend), Playwright (E2E)
*   **Containerization & CI/CD:** Docker, Docker Compose, GitHub Actions

---

## 🚀 Getting Started

For instructions on how to set up and run the application, please see the **[Installation Guide](./docs/installation_guide.md)**.

To learn how to use the application's features, refer to the **[User Guide](./docs/user_guide.md)**.

## 👨‍💻 For Developers

This project was built with a strong emphasis on developer experience and maintainability. If you're interested in the technical details or want to contribute, please check out the following resources:

*   **[Developer Guide](./developer_guide.md):** Instructions for setting up a development environment (both Docker and native), running tests, and understanding the local development workflow.
*   **[Contributing Guide](./CONTRIBUTING.md):** Our guide for contributing to the project, including our AI-assisted development process.
*   **[Architecture Overview](./docs/architecture.md):** A high-level look at the system's design.

---

## ⚠️ Disclaimer

### Data Sources

ArthSaarthi uses publicly available data from the following sources for asset master data and market information:

*   **[NSDL (National Securities Depository Limited)](https://nsdl.co.in/)** - Debt instruments master data
*   **[BSE (Bombay Stock Exchange)](https://www.bseindia.com/)** - Equity and debt bhavcopy, bond data, index data
*   **[NSE (National Stock Exchange)](https://www.nseindia.com/)** - Equity bhavcopy, debt listings
*   **[Upstox Developer API](https://upstox.com/developer/api-documentation/)** - Public unauthenticated historical market candles, trading holidays, and instrument master metadata
*   **[ICICI Direct](https://www.icicidirect.com/)** - Security master data (fallback source)

This application downloads and processes publicly available data from these exchanges for informational purposes only. ArthSaarthi is not affiliated with, endorsed by, or sponsored by any of these organizations.

### Financial Advice Notice

**ArthSaarthi is not a registered investment advisor.** The information provided by this application is for general informational and educational purposes only and should not be construed as financial, investment, tax, or legal advice.

*   All investment decisions should be made in consultation with a qualified financial advisor.
*   Past performance is not indicative of future results.
*   The data presented may contain errors or inaccuracies; always verify with official sources.
*   Users are solely responsible for their investment decisions.

---

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.
