﻿# Project Handoff Document: Personal Portfolio Management System

**Date:** 2025-08-03
**Prepared By:** Gemini Code Assist

---

## 1. Project Overview

The Personal Portfolio Management System (PMS) is a full-stack web application designed to help users track and analyze their investment portfolios. It provides a consolidated view of assets, calculates performance metrics, and offers data visualizations to help users make informed financial decisions.

The application is built with a modern tech stack, featuring a FastAPI backend and a React/TypeScript frontend, all containerized with Docker for easy setup and deployment.

---

## 2. Current Status: Pilot Release Complete

The project has successfully completed its **Pilot Release (v0.2.0)** and the backend for the **Automated Data Import (v0.3.0)** feature. All Minimum Viable Product (MVP) and initial advanced features are implemented and stable.

*   **All test suites are passing:**
    *   Backend (Pytest): 67/67 passed
    *   Frontend (Jest/RTL): 56/56 passed
    *   End-to-End (Playwright): All critical user flows are validated and passing.
*   The application is considered stable and ready for the frontend implementation of the data import feature.

---

## 3. Key Implemented Features

*   **Core User Authentication:** Secure JWT-based login for standard users and an initial administrator setup flow.
*   **Basic Administration:** Admins can perform CRUD operations on users.
*   **Portfolio & Transaction Management:** Users can create multiple portfolios and manually add transactions for Stocks, ETFs, and Mutual Funds.
*   **On-the-fly Asset Creation:** Users can add new assets not present in the pre-seeded database directly from the transaction modal.
*   **Dynamic Dashboard:**
    *   Consolidated view of total portfolio value.
    *   Calculation of Realized and Unrealized Profit/Loss.
    *   Asset allocation pie chart.
    *   Historical portfolio value line chart.
    *   Top daily market movers table.
*   **Advanced Portfolio Analytics (New in v0.2.0):**
    *   The Portfolio Detail page now includes an "Advanced Analytics" card.
    *   Calculates and displays the **XIRR (Extended Internal Rate of Return)**.
    *   Calculates and displays the **Sharpe Ratio**.
*   **Automated Data Import (Backend Only):** A full backend workflow for uploading, parsing, previewing, and committing transaction data from CSV files.

---

## 4. Technology Stack

*   **Backend:** Python, FastAPI, SQLAlchemy (ORM), Pydantic, PostgreSQL, Redis (for caching, if implemented).
*   **Frontend:** React, TypeScript, Vite, Tailwind CSS, React Query (for state management), Chart.js (for visualizations).
*   **Testing:**
    *   **Backend:** `pytest`
    *   **Frontend:** `jest`, `react-testing-library`
    *   **End-to-End:** `playwright`
*   **Infrastructure:** Docker, Docker Compose.

---

## 5. Getting Started

1.  **Prerequisites:** Docker and Docker Compose must be installed.
2.  **Run the application:** From the project root, run:
    ```bash
    docker-compose up --build db backend frontend
    ```
3.  **Initial Setup:** Navigate to `http://localhost:3000`. If it's the first run, you will be prompted to create an initial administrator account.

---

## 6. Running the Test Suites

*   **Backend Unit Tests:**
    ```bash
    docker-compose run --rm test
    ```
*   **Frontend Unit Tests:**
    ```bash
    docker-compose run --rm frontend npm test
    ```
*   **End-to-End Tests:**
    ```bash
    docker-compose -f docker-compose.yml -f docker-compose.e2e.yml up --build --abort-on-container-exit db redis backend frontend e2e-tests
    ```

---

## 7. Key Documentation

All project documentation is located in the `/docs` directory. Key files for new team members include:

*   `README.md`: High-level overview and setup instructions.
*   `product_backlog.md`: The official source of truth for feature requirements.
*   `code_flow_guide.md`: A deep dive into the application's data flow for key features.
*   `troubleshooting.md`: Solutions for common setup and runtime issues.
*   `LEARNING_LOG.md`: A log of key architectural decisions and lessons learned.
*   `bug_reports.md`: The complete history of all bugs filed and resolved.