# Developer Guide

This guide provides instructions and best practices for developers working on the ArthSaarthi project.

This guide covers two primary development workflows:
1.  **Docker-Based Development:** Uses Docker for a consistent, containerized environment that mirrors production.
2.  **Native (Dockerless) Development:** Runs the services directly on your host machine for maximum control.

---

## 1. Docker-Based Development

### Prerequisites

*   **Docker:** Get Docker
*   **Docker Compose:** Install Docker Compose

### Environment Setup

1.  **Clone the repository.**
2.  **Run the configuration script** to create the necessary `.env` files:
    ```bash
    ./configure.sh
    ```
    You will be prompted to edit `backend/.env.prod` to set `CORS_ORIGINS`. For local development, `http://localhost:3000` is usually sufficient.

### Running the Application

You can run the application in two primary modes:

**A) Default Mode (PostgreSQL + Redis)**

This is the full production-like setup.

```bash
docker-compose up --build
```
This command starts the `backend`, `frontend`, `db` (PostgreSQL), and `redis` services. The frontend will be available at `http://localhost:3000`.

**B) SQLite Mode (Simplified)**

This mode is ideal for quick development tasks as it does not require external database or cache services. It uses SQLite and a file-based cache, and enables hot-reloading for both the backend and frontend.

```bash
docker compose -f docker-compose.desktop.yml -f docker-compose.override.yml up --build
```
*   **Frontend (with hot-reloading):** `http://localhost:3000`
*   **Backend (with hot-reloading):** `http://localhost:8000`

### Running Tests with Docker


These commands run tests inside isolated Docker containers, which is the most reliable way to replicate the CI environment.

**For a faster and more comprehensive local testing experience, we strongly recommend using the Native (Dockerless) testing script described in the next section.**
*   **Backend Tests (PostgreSQL):**
    ```bash
    docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm test
    ```
*   **Backend Tests (SQLite/Desktop Mode):**
    ```bash
    docker compose -f docker-compose.yml -f docker-compose.test.desktop.yml run --build --rm test-desktop
    ```
*   **Frontend Unit Tests:**
    ```bash
    docker compose run --rm frontend npm test
    ```
*   **End-to-End (E2E) Tests (PostgreSQL):**
    ```bash
    docker compose -f docker-compose.yml -f docker-compose.e2e.yml up --build --abort-on-container-exit
    ```
*   **End-to-End (E2E) Tests (SQLite):**
    ```bash
    docker compose -f docker-compose.e2e.sqlite.yml up --build --abort-on-container-exit
    ```
---

## 2. Native (Dockerless) Development
This approach allows you to run the services directly on your host machine.

### Prerequisites
 
*   **Python:** Version 3.9 or higher.
*   **Node.js:** Version 18.x or higher (which includes `npm`).
*   **Git:** For cloning the repository.
*   **(Optional) PostgreSQL Server:** If you choose to use PostgreSQL instead of SQLite. 
*   **(Optional) PostgreSQL Server:** If you choose to use PostgreSQL instead of SQLite.

### Environment Setup

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd pms
    ```
2.  **Backend Setup:**
    - Navigate to the backend directory: `cd backend`
    - Create and activate a Python virtual environment:
        - **Linux/macOS:** `python3 -m venv venv && source venv/bin/activate`
        - **Windows:** `python -m venv venv && .\venv\Scripts\activate`
    - Install dependencies: `pip install -r requirements-dev.in`
    - Create a `.env` file by copying the example: `cp .env.example .env`
    - **Edit `backend/.env`:**
        - For **SQLite** (recommended for simplicity): Set `DATABASE_TYPE=sqlite` and `CACHE_TYPE=disk`.
        - For **PostgreSQL**: Set `DATABASE_TYPE=postgres`, `CACHE_TYPE=redis`, and update `DATABASE_URL` and `REDIS_URL` to point to your local instances.

3.  **Frontend Setup:**
    - Navigate to the frontend directory: `cd frontend`
    - Install dependencies: `npm install`
    - Create a local environment file: `touch .env.local`
    - **Edit `frontend/.env.local`** to tell the Vite dev server where the backend is running:
        ```
        VITE_API_PROXY_TARGET=http://localhost:8000
        ```

### Running the Application

You will need to run the backend and frontend servers in two separate terminal windows. 

1.  **Start the Backend Server:**
    - In a terminal, navigate to the `backend/` directory and ensure your virtual environment is activated.
    - Run the startup script: `./entrypoint.sh`
    - The backend will be running at `http://localhost:8000`.

2.  **Start the Frontend Server:**
    - In a second terminal, navigate to the `frontend/` directory.
    - Run the development server: `npm run dev`
    - The frontend will be accessible at `http://localhost:3000`.

### Running Tests (Native)

For a faster feedback loop without Docker, a comprehensive script is provided to run all linters and tests.

```bash
./run_local_tests.sh
```

This script is highly configurable, allowing you to run the entire suite or target specific parts for faster feedback

Running a Specific Test Suite:  
* Run the entire suite: ./run_local_tests.sh all 
* Run only linters: ./run_local_tests.sh lint 
* Run only backend tests: ./run_local_tests.sh backend 
* Run only frontend tests: ./run_local_tests.sh frontend 
* Run only E2E tests: ./run_local_tests.sh e2e 
* Run only migration tests: ./run_local_tests.sh migrations 
* Use a PostgreSQL database: ./run_local_tests.sh backend --db postgres 
* See all options: ./run_local_tests.sh --help 
 
Running a Single Test File or Function: 
 
You can also pass arguments directly to the underlying test runner (pytest for backend, playwright for E2E). 
* Run a single backend test file: ./run_local_tests.sh backend app/tests/api/v1/test_holdings.py 
* Run a single E2E test file: ./run_local_tests.sh e2e tests/portfolio-and-dashboard.spec.ts

---

## 3. Architectural Overview

The application is built with a modern web stack, featuring a FastAPI backend and a React (Vite) frontend.

### Backend

The backend is a standard layered application:
- **API Layer (`app/api`):** Defines the RESTful API endpoints using FastAPI routers.
- **CRUD Layer (`app/crud`):** Contains the core business logic and database interactions.
- **Database Layer (`app/db`):** Defines the SQLAlchemy models and database session management.
- **Schemas (`app/schemas`):** Pydantic models for data validation and serialization.

### Adding New Asset Types

The application supports two main types of assets:

1.  **Transaction-Based Assets:** These are assets like Stocks and Mutual Funds, where the holding is calculated by processing a series of BUY and SELL transactions.
2.  **Non-Transaction-Based Assets:** These are assets like Fixed Deposits, Bonds, and PPF accounts. They are added as a single entity and their value is calculated based on their own internal logic (e.g., compound interest), not from transactions.

To add a new **Non-Transaction-Based Asset Type**:

1.  **Create a new SQLAlchemy model** in `app/models/` (e.g., `app/models/new_asset.py`). This model should have a one-to-one relationship with the `Asset` model.
2.  **Create a new Pydantic schema** in `app/schemas/` for the new asset's creation and data representation.
3.  **Add a new Alembic migration** to create the new database table.
4.  **Create a new CRUD function** in `app/crud/crud_fixed_income.py` (or a new CRUD file if appropriate) to handle the creation of the new asset.
5.  **Add a new API endpoint** in `app/api/v1/endpoints/fixed_income.py` to expose the creation logic.
6.  **Update `crud.holding.get_portfolio_holdings_and_summary`** to include the new asset type in the portfolio holdings and summary calculations. This involves adding logic to the `_process_fixed_income_assets` function.
7.  **Update the frontend** to include a new modal and form for creating the asset, and a new row component in the `HoldingsTable` to display it.

---

## 4. Code Quality & CI/CD

*   **Linting:** We use `ruff` for the backend and `eslint` for the frontend. Please run the linters before committing.
*   **CI/CD:** Our GitHub Actions workflow (in `.github/workflows/ci.yml`) runs all linters and tests on every push and pull request to the `main` branch. All checks must pass before a PR can be merged.

## 4. Further Reading

*   **Contributing Guide:** Our guide for contributing to the project, including our AI-assisted development process.
*   **Testing Strategy:** A detailed explanation of our multi-layered testing approach.
*   **Troubleshooting Guide:** Solutions for common development and runtime issues."
