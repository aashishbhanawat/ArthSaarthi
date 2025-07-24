﻿﻿﻿﻿﻿﻿﻿﻿﻿# Personal Portfolio Management System (PMS)

This project is a web-based application designed to help users manage their personal investment portfolios. It allows tracking of various assets, providing performance insights and analytics.

This project is being developed with the guidance of an AI Master Orchestrator, following an Agile SDLC.

## Features Implemented

*   **Authentication:** Secure initial admin setup, user login/logout, and JWT-based session management.
*   **User Management:** A dedicated, admin-only dashboard for performing CRUD operations on all users.
*   **Portfolio & Transaction Management:** A stable and fully tested set of APIs and UI components for creating portfolios and transactions, with validation to ensure data integrity.
*   **Dashboard:** A dynamic dashboard that displays a summary of the user's total portfolio value, an interactive portfolio history chart, and an asset allocation pie chart.
## Technology Stack

-   **Backend:** Python with [FastAPI](https://fastapi.tiangolo.com/)
-   **Frontend:** JavaScript with [React](https://reactjs.org/)
-   **Database:** [PostgreSQL](https://www.postgresql.org/)
-   **Deployment:** [Docker](https://www.docker.com/)

## Data Source Disclaimer

This application retrieves financial data from publicly available sources via the `yfinance` library, which is not an official API from Yahoo Finance.

-   **For Informational Purposes Only:** All data is provided for personal, informational, and non-commercial use only. It should not be considered professional financial advice.
-   **No Guarantees:** The availability, accuracy, and timeliness of the data are not guaranteed. The underlying public APIs may change or become unavailable at any time.
-   **Not for Trading:** Do not use the data provided by this application to make financial trading decisions. Always consult official sources or a qualified financial advisor.

## Running the Project

This project is fully containerized using Docker and Docker Compose for a consistent and streamlined development experience.

### Prerequisites
*   Docker
*   Docker Compose

### 1. Environment Configuration

The project uses `.env` files for configuration.

*   **Backend:** Create a file at `backend/.env`. You can copy `backend/.env.example` as a template. The default values are suitable for local development.
*   **Frontend:** The frontend is configured to use a proxy, so no `.env` file is needed for local development.

### 2. Build and Run the Application

From the project's root directory, run the following command to start the application services:
```bash
docker-compose up --build db backend frontend
```
This command will build the Docker images and start only the necessary services for the application to run. The backend will wait for the database to be healthy before starting.

### 3. Accessing the Services

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