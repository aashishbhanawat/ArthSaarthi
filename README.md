# ArthSaarthi - Personal Portfolio Management System

<!-- Note: Replace YOUR_USERNAME/YOUR_REPO with your actual GitHub repository path -->
[![CI/CD Status](https://github.com/aashishbhanawat/pms/actions/workflows/ci.yml/badge.svg)](https://github.com/aashishbhanawat/pms/actions/workflows/ci.yml)
<!-- The badges below are placeholders. To make them dynamic, you would need a service that generates badges from your test coverage reports (e.g., Codecov, Coveralls). -->
[![Backend Tests](https://img.shields.io/badge/Backend_Tests-Passing-brightgreen)](#)
[![Frontend Tests](https://img.shields.io/badge/Frontend_Tests-Passing-brightgreen)](#)
[![E2E Tests](https://img.shields.io/badge/E2E_Tests-Passing-brightgreen)](#)

---

## 1. Overview

**ArthSaarthi** is a full-stack web application designed to help users manage their personal investment portfolios. It is built with a Python/FastAPI backend, a TypeScript/React frontend, and a PostgreSQL database, all containerized with Docker for consistent and reliable deployment.

The project was developed following a rigorous, AI-assisted Agile SDLC, with a strong emphasis on automated testing, comprehensive documentation, and iterative feature implementation.

## 2. Key Features

*   **Secure Authentication:** Initial admin setup, JWT-based login/logout, and automatic session termination on token expiration.
*   **Comprehensive User Management:** Admin-only dashboard for full CRUD operations on all users.
*   **Dynamic Dashboard:** Consolidated view of total portfolio value, realized/unrealized P/L, top daily market movers, and interactive charts for portfolio history and asset allocation.
*   **Advanced Portfolio Analytics:** Calculation and display of **XIRR (Extended Internal Rate of Return)** and **Sharpe Ratio** at both the portfolio and individual asset level.
*   **Full Portfolio & Transaction Management:**
    *   Full CRUD functionality for portfolios and transactions.
    *   A redesigned portfolio page showing a consolidated holdings view with sorting.
    *   A **Holdings Drill-Down View** to inspect the specific transactions that constitute a current holding.
*   **Automated Data Import:** A full-stack feature with a complete backend workflow for uploading, parsing, previewing, and committing transaction data from CSV files.

## 3. Technology Stack

*   **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL, SQLite, Redis, DiskCache
*   **Frontend:** TypeScript, React, Vite, React Query, Tailwind CSS
*   **Testing:** Pytest (Backend), Jest & React Testing Library (Frontend), Playwright (E2E)
*   **Containerization:** Docker, Docker Compose

## 4. 🚀 How to Run the Project

### Prerequisites

*   Docker
*   Docker Compose

### Environment Setup

1.  **Clone the repository.**
2.  **Run the configuration script:**
    ```bash
    ./configure.sh
    ```
    This will create the necessary `.env` files and generate a secure secret key. You will be prompted to edit the `CORS_ORIGINS` setting, which is a crucial security step.
3.  **For frontend development (optional):** If you need to access the Vite dev server from a different domain or IP address, create a `frontend/.env` file and add the `ALLOWED_HOSTS` variable:
    ```
    ALLOWED_HOSTS=your.domain.com,192.168.1.100
    ```
4.  **Configure Caching (optional):** The application uses Redis for caching by default. For non-Docker or simplified deployments, you can switch to a file-based cache by setting the following environment variable in your `backend/.env` file:
    ```
    CACHE_TYPE=disk
    ```

### Running with PostgreSQL (Default)

To start the application services (database, backend, frontend), run:

```bash
docker compose up --build
```

*   Frontend will be available at `http://localhost:3000`
*   Backend API will be available at `http://localhost:8000`

**Note on Database Resets:** To completely reset the database, run `docker compose down -v`. After this, you will need to perform the initial admin setup again in the browser.

### Running with SQLite (Simplified Setup)

For a simpler setup that does not require a separate PostgreSQL or Redis instance, you can run the application using SQLite and a file-based cache. This is ideal for local development or simple deployments.

1.  **Run the configuration script** as described above.
2.  **Start the application using the SQLite override file:**

    ```bash
    docker compose -f docker-compose.yml -f docker-compose.sqlite.yml up --build
    ```

    This will start the backend and frontend services. The backend will use a persistent SQLite database file (`arthsaarthi.db`) and `diskcache` for caching, removing the need for the `db` and `redis` containers.

### Building the Native Desktop Application

The application can be packaged as a standalone desktop application for Windows, macOS, and Linux using Electron and PyInstaller.

To build the desktop application, run the following script:

```bash
./scripts/build-desktop.sh
```

This script will:
1.  Bundle the Python backend into a single executable.
2.  Build the React frontend.
3.  Package everything into a native installer for your current operating system.

The final installer will be located in the `frontend/release` directory.

### Running the Test Suites

**1. Backend Unit & Integration Tests:**

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm test
```

**2. Frontend Unit & Integration Tests:**

```bash
docker compose run --rm frontend npm test
```

**3. End-to-End (E2E) Tests:**

This command starts a fully isolated test environment and runs the Playwright tests.

```bash
docker compose -f docker-compose.yml -f docker-compose.e2e.yml up --build --abort-on-container-exit
```

**4. Running All Checks Locally (Without Docker):**

For a development environment without Docker, a comprehensive script is provided to run all linters and tests. This is the recommended way to validate changes locally before committing.

```bash
./run_e2e_local.sh
```

This script will automatically handle dependencies, start the necessary services on dynamic ports, run all backend, frontend, and E2E tests, and clean up afterwards. For more details on the individual commands, see the `prompt/AGENTS.md` guide.

## 5. Project Documentation

This project emphasizes comprehensive documentation to ensure clarity and maintainability.

*   **System Architecture:** High-level overview of the system design.
*   **User Guide:** Instructions on how to use the application's features.
*   **Testing Strategy:** Detailed explanation of our multi-layered testing approach.
*   **Bug Reports:** A complete log of all bugs discovered and their resolutions.
*   **Workflow History:** A chronological log of the AI-assisted development process.
*   **Troubleshooting Guide:** Solutions for common development and runtime issues.
*   **Feature Plans:** Detailed plans for each implemented feature.

## 6. Contributing

Please see the CONTRIBUTING.md file for details on our development process and how to contribute.