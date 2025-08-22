# ArthSaarthi - Personal Portfolio Management System

[![CI/CD Status](https://github.com/aashishbhanawat/pms/actions/workflows/ci.yml/badge.svg)](https://github.com/aashishbhanawat/pms/actions/workflows/ci.yml)
[![Backend Tests](https://img.shields.io/badge/Backend_Tests-Passing-brightgreen)](#)
[![Frontend Tests](https://img.shields.io/badge/Frontend_Tests-Passing-brightgreen)](#)
[![E2E Tests](https://img.shields.io/badge/E2E_Tests-Passing-brightgreen)](#)

---

**ArthSaarthi** is a self-hostable, privacy-focused application designed to help users manage their personal investment portfolios. It provides a comprehensive suite of tools for tracking assets, analyzing performance, and making informed financial decisions.

The application can be run as a full-stack web service using Docker, or as a simple, single-user **desktop application** that requires no external database, making it accessible to both technical and non-technical users.

The project was developed following a rigorous, AI-assisted Agile SDLC, with a strong emphasis on automated testing, comprehensive documentation, and iterative feature implementation.

<!-- Optional: Add a link to a live demo if you have one -->
<!-- **[Live Demo](https://your-demo-link.com)** -->

## ✨ Features

### Currently Available

*   **Secure Authentication & User Management:** Initial admin setup, JWT-based login/logout, and an admin-only dashboard for full CRUD operations on users.
*   **Comprehensive Dashboard:** Get a bird's-eye view of your financial health with a dynamic dashboard showing total portfolio value, realized/unrealized P&L, top daily market movers, and interactive charts for portfolio history and asset allocation.
*   **Advanced Portfolio Analytics:** Go beyond simple returns with on-demand calculation and display of **XIRR (Extended Internal Rate of Return)** and **Sharpe Ratio** at both the portfolio and individual asset level.
*   **Detailed Portfolio & Transaction Management:**
    *   Create and manage multiple portfolios with full CRUD functionality for transactions.
    *   A redesigned portfolio page showing a consolidated holdings view with sorting.
    *   A unique **Holdings Drill-Down View** to inspect the specific transactions that constitute a current holding.
*   **Automated Data Import:** Drastically reduce manual entry with a full-stack feature for uploading, parsing, previewing, and committing transaction data from CSV files (supports Zerodha, ICICI Direct, and generic formats).

### On the Horizon (Future Features)

*   **Advanced Asset Support:** Track everything from Employee Stock Plans (RSUs/ESPPs) and Fixed Deposits (FDs) to government schemes like PPF and NPS.
*   **Corporate Actions & Income Tracking:** Automatically handle dividends, stock splits, and bonuses, and track income from interest payments.
*   **Deeper Analytics & Reporting:** Generate capital gains reports for tax filing, benchmark your portfolio against market indices, and analyze diversification by sector, geography, and more.
*   **Goal-Oriented Planning:** Define financial goals (e.g., "Retirement", "House Down Payment"), link assets to them, and track your progress with projections.
*   **AI-Powered Insights:** Leverage AI to get suggestions for tax-loss harvesting, portfolio rebalancing, and receive a personalized daily digest of your financial world.
*   **Market Insights:** Create watchlists, get relevant news feeds, and perform deep-dive research on individual assets.

## 🛠️ Technology Stack

*   **Backend:** Python, FastAPI, SQLAlchemy, Alembic (Migrations)
*   **Frontend:** TypeScript, React, Vite, React Query, Tailwind CSS
*   **Database:** PostgreSQL, SQLite
*   **Caching:** Redis, DiskCache
*   **Testing:** Pytest (Backend), Jest & React Testing Library (Frontend), Playwright (E2E)
*   **Containerization & CI/CD:** Docker, Docker Compose, GitHub Actions

---

## 🚀 Getting Started

For instructions on how to set up and run the application, please see the **[Installation Guide](./installation_guide.md)**.

To learn how to use the application's features, refer to the **[User Guide](./docs/user_guide.md)**.

## 👨‍💻 For Developers

We welcome contributions! If you're interested in the technical details or want to contribute to the project, please check out the following resources:

*   **Developer Guide:** Instructions for setting up a development environment, running tests, and understanding the local development workflow.
*   **Contributing Guide:** Our guide for contributing to the project, including our AI-assisted development process.
*   **Architecture Overview:** A high-level look at the system's design.

---

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.
