# ArthSaarthi - Personal Portfolio Management System

[![CI/CD Status](https://github.com/aashishbhanawat/ArthSaarthi/actions/workflows/ci.yml/badge.svg)](https://github.com/aashishbhanawat/ArthSaarthi/actions/workflows/ci.yml)
[![Backend Tests](https://img.shields.io/badge/Backend_Tests-131/131-brightgreen)](#)
[![Frontend Tests](https://img.shields.io/badge/Frontend_Tests-159/159-brightgreen)](#)
[![E2E Tests](https://img.shields.io/badge/E2E_Tests-21/21-brightgreen)](#)

---

**ArthSaarthi** is a self-hostable, privacy-focused application designed to help users manage their personal investment portfolios. It provides a comprehensive suite of tools for tracking assets, analyzing performance, and making informed financial decisions.

The application is designed for flexibility and can be deployed in two ways: as a multi-user **web service** using Docker for self-hosting, or as a simple, single-user **desktop application** that requires no external database, making it accessible to both technical and non-technical users.

The project was developed following a rigorous, AI-assisted Agile SDLC, with a strong emphasis on automated testing, comprehensive documentation, and iterative feature implementation.

<!-- Optional: Add a link to a live demo if you have one -->
<!-- **[Live Demo](https://your-demo-link.com)** -->

## ✨ Core Features

*   **Secure Authentication & Administration:** JWT-based authentication, initial admin setup, a full admin dashboard for user management (CRUD), a backend **Audit Logging Engine** to record all sensitive events, and a dedicated **User Profile Page** to manage your account.
*   **Dynamic Dashboard:** Get a bird's-eye view of your financial health with a dashboard showing total portfolio value, realized/unrealized P&L, top daily market movers, and interactive charts for portfolio history and asset allocation.
*   **Advanced Portfolio Analytics:** On-demand calculation and display of **XIRR (Extended Internal Rate of Return)** and **Sharpe Ratio** at both the portfolio and individual asset levels.
*   **Comprehensive Portfolio & Transaction Management:**
    *   Full CRUD functionality for portfolios.
    *   Full CRUD functionality for transactions, including a dedicated, filterable **Transaction History** page and support for logging corporate actions (**Dividends, Stock Splits, Bonus Issues**).
    *   Full CRUD and tracking for **Fixed Deposits (FDs)**, **Recurring Deposits (RDs)**, **Public Provident Fund (PPF)** accounts, and **Bonds** with detailed analytics.
*   **Consolidated Holdings View:** A redesigned portfolio page that shows a consolidated holdings table with sorting, replacing a simple transaction list.
*   **Sectioned Holdings Table:** A redesigned holdings table that groups assets by class into collapsible sections for a clearer overview.
*   **Mutual Fund Dividend Tracking:** Manually log cash or reinvested dividends for mutual fund holdings.
*   **Holdings Drill-Down:** Click on any holding to see a detailed modal with its constituent buy transactions, calculated using FIFO logic.
*   **Automated Data Import:** A full-stack workflow for uploading, parsing, previewing, and committing transaction data from CSV files.
    *   Includes pre-built parsers for Zerodha, ICICI Direct, and a generic format.
    *   Features an advanced UI for on-the-fly **asset alias mapping** for unrecognized ticker symbols.
*   **Goal Planning & Tracking (Core):** Define financial goals, link assets or portfolios to them, and track your current progress.
*   **Market Insights (Watchlists):** Create and manage custom watchlists to monitor assets you don't own.
*   **Flexible Deployment:**
    *   **Server Mode:** A multi-user web service using Docker with PostgreSQL and Redis.
    *   **Desktop Mode:** A single-user, privacy-focused native application using an encrypted SQLite database and a file-based cache.
*   **Performance:** Expensive analytics and holdings calculations are cached to improve UI responsiveness and reduce server load.

### On the Horizon (Future Features)

*   **Corporate Actions & Income Tracking:** Automatically handle dividends, stock splits, and bonuses, and track income from interest payments.
*   **Deeper Analytics & Reporting:** Generate capital gains reports for tax filing, benchmark your portfolio against market indices, and analyze diversification by sector, geography, and more.
*   **Goal-Oriented Planning:** Define financial goals (e.g., "Retirement", "House Down Payment"), link assets to them, and track your progress with projections.
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

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.
