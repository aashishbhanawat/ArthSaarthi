﻿# Personal Portfolio Management System (PMS)

This project is a web-based application designed to help users manage their personal investment portfolios. It allows tracking of various assets, providing performance insights and analytics.

This project is being developed with the guidance of an AI Master Orchestrator, following a rigorous, test-driven, and well-documented Agile SDLC.

## Features Implemented

*   **Secure Authentication:**
    *   Initial admin setup for the first user.
    *   Standard user login/logout with JWT-based session management.
    *   Automatic logout on token expiration.
*   **Comprehensive User Management:**
    *   Admin-only dashboard for full CRUD operations on all users.
*   **Dynamic Dashboard:**
    *   Consolidated view of total portfolio value.
    *   Realized and Unrealized Profit/Loss calculations.
    *   Top daily market movers.
    *   Interactive portfolio history and asset allocation charts.
*   **Full Portfolio & Transaction Tracking:**
    *   Create and manage multiple portfolios.
    *   Add transactions with on-the-fly asset creation for unlisted tickers.
    *   Business logic validation to prevent invalid transactions (e.g., selling more than you own).

## Technology Stack

-   **Backend:** Python with [FastAPI](https://fastapi.tiangolo.com/)
-   **Frontend:** JavaScript with [React](https://reactjs.org/)
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
docker-compose run --rm test
```

### Frontend Tests

To run the frontend test suite using Jest and React Testing Library, use the following command from the root directory:

    ```bash
    docker-compose run --rm frontend npm test
    ```

## Contributing

Please read `CONTRIBUTING.md` for details on our development process. Our rigorous development process, including our AI-assisted workflow and testing standards, is detailed in `docs/testing_strategy.md` and `docs/workflow_history.md`.

See `docs/troubleshooting.md` for solutions to common setup and runtime issues.