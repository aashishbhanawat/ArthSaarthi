﻿﻿﻿# Personal Portfolio Management System (PMS)

This project is a web-based application designed to help users manage their personal investment portfolios. It allows tracking of various assets, providing performance insights and analytics.

This project is being developed with the guidance of an AI Master Orchestrator, following a rigorous, test-driven, and well-documented Agile SDLC.

## Features Implemented

*   **Secure Authentication:**
    -   Initial admin setup for the first user.
    -   Standard user login/logout with JWT-based session management.
    -   Automatic logout on token expiration.
*   **Comprehensive User Management:**
    -   Admin-only dashboard for full CRUD operations on all users.
*   **Dynamic Dashboard:**
    -   Consolidated view of total portfolio value.
    -   Realized and Unrealized Profit/Loss calculations.
    -   Top daily market movers.
    -   Interactive portfolio history and asset allocation charts.
*   **Advanced Portfolio Analytics:**
    -   Calculation and display of XIRR (Extended Internal Rate of Return) and the Sharpe Ratio.
*   **Full Portfolio & Transaction Tracking:**
    -   Create and manage multiple portfolios.
    -   Full CRUD (Create, Read, Update, Delete) functionality for transactions.
    -   On-the-fly asset creation for unlisted tickers during transaction entry.
    -   Business logic validation to prevent invalid transactions (e.g., selling more than you own).
*   **Automated Data Import:** A full-stack feature with a complete workflow for uploading, parsing, previewing, and committing transaction data from CSV files.

## Technology Stack

-   **Backend:** Python with [FastAPI](https://fastapi.tiangolo.com/)
-   **Frontend:** TypeScript with [React](https://reactjs.org/)
-   **Database:** [PostgreSQL](https://www.postgresql.org/)
-   **Deployment:** [Docker](https://www.docker.com/)

## Project Structure

The project follows a standard monorepo structure with a clear separation of concerns.

```
pms/
├── backend/         # FastAPI application
├── docs/            # All project documentation
├── frontend/        # React application
└── docker-compose.yml # Main orchestration file
```

For a more detailed breakdown, please see the [System Architecture Document](./docs/architecture.md).

---

> [!IMPORTANT]
> **Data Source Disclaimer**
> This application is for informational and personal use only and is not intended for financial trading. See the full [Disclaimer](./docs/DISCLAIMER.md).

---

## 🚀 How to Self-Host (Pilot Release)

This guide is for users who want to run their own instance of the application using Docker.

### Prerequisites

*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/)

### Step 1: Download the Release

Download the `pms-pilot-vX.Y.Z.zip` or `.tar.gz` file from the latest GitHub Release and unzip it.

### Step 2: Configure Your Instance

Run the configuration script. This will create your unique production environment file.

```bash
chmod +x *.sh
./configure.sh
```

The script will create a file at `backend/.env.prod`. **You must edit this file** and set the `CORS_ORIGINS` variable to the domain name or IP address you will use to access the application.

### Step 3: Start the Application

Run the start script. This will build the Docker images and start all the necessary services in the background.

```bash
./start.sh
```

### Step 4: Initial Admin Setup

1.  Open your web browser and navigate to `http://localhost` (or the IP/domain you configured in Step 2).
2.  You will be presented with an "Initial Setup" screen to create your admin account.
3.  After setup, you will be redirected to the login page. Log in with the credentials you just created.

### Managing Your Instance

*   **To stop the application:** `./stop.sh`
*   **To view live logs:** `./logs.sh`
*   **To update to a new version:** Stop the app, overwrite the files with the new release, and run `./start.sh` again. Your data is stored in a Docker volume and will be preserved.
*   **To learn how to use the application's features, see the ➡️ User Guide.**

---

## Running the Project

This project is fully containerized using Docker and Docker Compose for a consistent and streamlined development experience.

### Prerequisites
*   Docker
*   Docker Compose

### 1. Environment Configuration

The project uses `.env` files for configuration.

*   **Backend:** Create a file at `backend/.env`. You can copy `backend/.env.example` as a template. The default values are suitable for local development.
*   **Frontend:** The frontend is configured to use a proxy, so no `.env` file is needed for local development.

> [!NOTE]
> If you are running the application for the first time with a fresh database, you will be directed to an initial setup page at `http://localhost:3000` to create the first admin user. If you reset the database later (`docker-compose down -v`), you will need to perform this setup again.

### 2. Build and Run the Application

From the project's root directory, run the following command to start the application services:

```bash
docker-compose up --build db backend frontend
```
This command will build the Docker images and start only the necessary services for the application to run. The backend will wait for the database to be healthy before starting.

### 3. Running Natively (Without Docker)
For users who cannot or prefer not to use Docker, a detailed guide for setting up and running the project natively is available. This requires manual installation of Python, Node.js, PostgreSQL, and Redis.

**➡️ [View the Native Setup Guide](./docs/native_setup_guide.md)**

### 4. Accessing the Services

*   **Frontend Application:** `http://localhost:3000`
*   **Backend API Docs (Swagger UI):** `http://localhost:8000/docs`

## Running Tests

### Backend Tests

The backend has a comprehensive test suite using `pytest`. To run the tests in an isolated container with a dedicated test database, use the following command from the root directory:

```bash
docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm test
```

### Frontend Tests

To run the frontend test suite using Jest and React Testing Library, use the following command from the root directory:

    ```bash
    docker-compose run --rm frontend npm test
    ```

### End-to-End (E2E) Tests

The E2E test suite runs using Playwright in a dedicated Docker environment. This command starts all necessary services, runs the tests, propagates the test exit code, and then automatically stops and removes the test containers.

```bash
docker-compose -f docker-compose.yml -f docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from e2e-tests db redis backend frontend e2e-tests
```
[!IMPORTANT]
The E2E and backend test suites use dedicated, isolated database volumes (`postgres_data_test`). They will **not** affect your development database. You only need to run `docker-compose down -v` when you want to completely reset your **development** environment.

## Development Utilities
### Seeding Sample Data
To populate the database with sample transactions for development and testing purposes, you can run the seeding script. This is particularly useful for testing features like the dashboard and advanced analytics. 
Note: This script will add data for the first user it finds in the database (typically the initial admin user). It is safe to run multiple times. 
```bashh 
docker-compose run --rm backend python -m app.scripts.seed_transactions 
```

### Dynamic Debugging

The application includes a dynamic debugging feature that can be enabled via environment variables to provide more verbose logging without changing the code. For detailed instructions on how to enable this for the backend and frontend, please see the Debugging Guide.


## Contributing

Please read `CONTRIBUTING.md` for details on our development process. Our rigorous development process, including our AI-assisted workflow and testing standards, is detailed in `docs/testing_strategy.md` and `docs/workflow_history.md`.

See `docs/troubleshooting.md` for solutions to common setup and runtime issues.