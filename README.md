﻿﻿﻿# Personal Portfolio Management System (PMS)

This project is a web-based application designed to help users manage their personal investment portfolios. It allows tracking of various assets, providing performance insights and analytics.

This project is being developed with the guidance of an AI Master Orchestrator, following an Agile SDLC.

## Features Implemented

*   **Core User Authentication:** Secure user registration and login. The first user registered is automatically designated as an administrator.
*   **User Management Dashboard:** A dedicated, admin-only interface for performing Create, Read, Update, and Delete (CRUD) operations on all users in the system.

*   **Portfolio & Transaction Management (Backend):** Backend APIs for creating portfolios and logging transactions for stocks, ETFs, and mutual funds.
## Technology Stack

-   **Backend:** Python with [FastAPI](https://fastapi.tiangolo.com/)
-   **Frontend:** JavaScript with [React](https://reactjs.org/)
-   **Database:** [PostgreSQL](https://www.postgresql.org/)
-   **Deployment:** [Docker](https://www.docker.com/)

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

From the project's root directory, run:
    ```bash
    docker-compose up --build
    ```
This command will build the Docker images and start the `db`, `backend`, and `frontend` services. The backend will wait for the database to be healthy before starting.

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

Please read CONTRIBUTING.md for details on our development process and the roles involved in this project.

See `docs/troubleshooting.md` for solutions to common setup and runtime issues.