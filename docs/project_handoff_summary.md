# Project Handoff Summary: Personal Portfolio Management System

**Date:** 2025-07-31

## 1. Project Overview & Status

*   **Goal:** To build a full-stack, containerized Personal Portfolio Management System (PMS) that allows users to manage their investment portfolios.
*   **Current Status:** The application is **stable and feature-complete for its pilot release**. It has been through a rigorous E2E testing and stabilization phase. All core features are functional, the UI is consistent, and the backend and frontend are fully covered by automated tests.
*   **Key Implemented Features:**
    *   **Authentication:** Secure initial admin setup, user login/logout, and secure session management using JSON Web Tokens (JWT).
    *   **User Management:** A dedicated, admin-only dashboard for performing CRUD operations on all users.
    *   **Portfolio & Transaction Management:** A stable and fully tested set of APIs and UI components for creating portfolios and transactions. Includes on-the-fly asset creation and validation to prevent invalid data entry (e.g., selling unowned assets).
    *   **Dashboard:** A dynamic dashboard that displays a summary of the user's total portfolio value, realized and unrealized P/L, top daily movers, an interactive portfolio history chart, and an asset allocation pie chart.

---

## 2. Technical Architecture

*   **Technology Stack:**
    *   **Backend:** Python with FastAPI
    *   **Frontend:** JavaScript with React and Vite
    *   **Database:** PostgreSQL
    *   **Deployment:** Docker & Docker Compose

*   **Directory Structure:** The project follows a standard monorepo structure with separate `backend/` and `frontend/` directories. Key subdirectories include:
    *   `backend/app/`: Contains the core FastAPI application, organized by `api` (endpoints), `crud` (database logic), `models` (SQLAlchemy), and `schemas` (Pydantic).
    *   `frontend/src/`: Contains the React application, organized by `pages`, `components`, `hooks`, `context`, and `services`.
    *   `docs/`: Contains all project documentation, including this handoff, bug reports, and workflow history.

*   **Key Architectural Patterns:**
    *   **Containerization:** The entire application is orchestrated via `docker-compose.yml`, ensuring a consistent development environment.
    *   **Backend Design:** The backend follows a clean, layered architecture. FastAPI is used for routing, Pydantic for data validation, and SQLAlchemy for ORM interaction. A repository pattern is implemented in the `crud` layer.
    *   **Frontend Design:** The frontend uses React Query for server state management, React Context for global UI state (e.g., authentication), and Tailwind CSS for styling.
    *   **Optimized External API Usage:** To manage reliance on the external financial data service (`yfinance`), the backend implements caching and request batching to minimize API calls, improve performance, and reduce the risk of rate-limiting.

---

## 3. Getting Started

### Prerequisites
*   Docker
*   Docker Compose

### Setup & Running

1.  **Configure Environment:** Create a `backend/.env` file (copy from `backend/.env.example`). The defaults are suitable for local development. No frontend `.env` is needed due to the Vite proxy.
2.  **Build and Run:** From the project root, run the following command to start the application services:
    ```bash
    docker-compose up --build db backend frontend
    ```
3.  **Access Services:**
    *   **Frontend:** `http://localhost:3000`
    *   **Backend API Docs:** `http://localhost:8000/docs`

### Running Tests

*   **Backend Tests:**
    ```bash
    docker-compose run --rm test
    ```
*   **Frontend Tests:**
    ```bash
    docker-compose run --rm frontend npm test
    ```
*   **End-to-End (E2E) Tests:** This command starts all necessary services, runs the tests, and then automatically shuts down.
    It returns the exit code from the test runner, which is essential for CI/CD pipelines. It also automatically stops and removes the test containers, so a separate `docker-compose down` is not required after a successful run.
    ```bash
    docker-compose -f docker-compose.yml -f docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from e2e-tests
    ```
    > [!IMPORTANT]  
    > The E2E test suite runs against a dedicated test database (`pms_db_test`) and **will not affect your development database** (`pms_db`). You do not need to run `docker-compose down -v` after running E2E tests. The `down -v` command is a destructive action that should only be used when you intentionally want to reset your development database.

---

## 4. Development Process & Key Learnings

This project was developed using a rigorous, AI-assisted workflow that evolved significantly over the project's lifecycle. The final, stable process is documented in detail in `docs/testing_strategy.md` and is crucial for any future development.

### Core Workflow: "Analyze -> Report -> Fix"

When a bug is discovered, we do not immediately attempt a fix. Instead, we follow a disciplined process:
1.  **Analyze:** Perform a rigorous root cause analysis (RCA) by examining the full stack trace and validating all dependencies involved in the error.
2.  **Report:** File a formal, de-duplicated bug report in `docs/bug_reports.md`.
3.  **Fix:** Request a targeted fix for the identified root cause.

### Key Learnings & Process Imperatives

Our development history revealed several critical patterns that this workflow is designed to prevent. Any new developer must be aware of these historical risks:

1.  **Risk: Configuration & Setup Errors.**
    *   **History:** A significant number of critical bugs were caused by missing dependencies, incorrect `.env` variables, or misconfigured build tools (e.g., the missing Tailwind CSS configuration).
    *   **Mitigation:** Our workflow now mandates a "foundation-first" approach. Before major work, we verify the build system and environment configuration.

2.  **Risk: Integration Mismatches.**
    *   **History:** The most common source of application-breaking bugs was a mismatch between the frontend and backend contracts (e.g., incorrect API URLs, mismatched data types like `float` vs. `Decimal`, inconsistent `localStorage` keys).
    *   **Mitigation:** The RCA process now requires validating the "contract" between components (e.g., checking the backend schema before fixing a frontend data handling issue).

3.  **Risk: E2E Environment Complexity.**
    *   **History:** A significant portion of the project was dedicated to debugging the E2E test environment. Issues arose from Docker networking, CORS policies, Vite proxy settings, and environment variable inheritance.
    *   **Mitigation:** The E2E test setup is now treated as a core feature. Any changes to the build system, Docker configuration, or environment variables must be validated against the E2E test suite.

4.  **Risk: Stale AI Context.**
    *   **History:** The AI assistant would occasionally work with outdated file information, leading to incorrect suggestions.
    *   **Mitigation:** The developer is the **source of truth**. The established process requires providing the AI with the latest file content to resynchronize its context when necessary.

---

## 5. Known Architectural Risks & Future Work
*   **Database Migrations:** The project uses **Alembic** for schema management. The entrypoint script for the backend service automatically runs `alembic upgrade head` on startup to apply the latest migrations. All database model changes must be accompanied by a new, versioned migration script to prevent schema drift.
*   **Configuration Management:** A strategy for managing secrets (e.g., `SECRET_KEY`) that supports both Docker and standalone deployments needs to be finalized for production readiness.
---

## 6. Next Steps

The application is stable and ready for further development. The next logical step is to begin planning for the next major feature from the requirements backlog.

1.  **Advanced Goal Planning & Tracking (FR13):** Allow users to define financial goals and track their progress.
2.  **Advanced Analytics (FR6):** Implement calculations for XIRR, Sharpe Ratio, and other performance metrics.
3.  **Data Import (FR7):** Implement the functionality to import transactions from broker statements.

---

*For additional details, please refer to the complete project documentation in the `/docs` directory.*