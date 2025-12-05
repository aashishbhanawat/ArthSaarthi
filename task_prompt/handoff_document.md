### Project Handoff Document: ArthSaarthi

#### 1. Project Goal & Current Status

*   **Goal:** To build a full-stack, containerized application, **ArthSaarthi**, with a robust, multi-layered testing strategy.
*   **Current Status:** The application is stable and feature-complete for the MVP and Release 2 backend requirements. All test suites (backend, frontend, E2E) are passing. The backend for the "Automated Data Import" feature is complete.
*   **Testing:** The project has a multi-layered testing strategy. A full suite of automated backend tests (`pytest`), frontend tests (`jest`), and **end-to-end tests (`Playwright`)** is stable and passing. This ensures reliability from individual components to complete user flows.
*   **Implemented Functionalities:**
    *   **Authentication:** Initial admin setup, secure user login/logout, and JWT-based session management.
    *   **User Management:** A dedicated, admin-only dashboard for performing Create, Read, Update, and Delete (CRUD) operations on all users.
    *   **Portfolio & Transaction Management:** Full CRUD for portfolios and transactions, including support for corporate actions (Splits, Bonuses, Dividends).
    *   **Asset Management:** On-the-fly asset creation and lookup.
    *   **Dashboard & Analytics:** Foundational endpoints for dashboard summary, historical performance, and asset allocation. (Note: Advanced calculations for P&L and XIRR including dividend income have been deferred to a future release to ensure stability).
    *   **Automated Data Import (Backend):** A full backend workflow for uploading, parsing, previewing, and committing transaction data from CSV files.



---

#### 2. Directory Structure

The project is organized into a clean, scalable monorepo structure.

*   `pms/`
    *   `backend/`: Contains the Python FastAPI application.
        *   `app/`: The main application package.
            *   `api/`: FastAPI routers and endpoints.
            *   `core/`: Core logic, including security (password hashing, JWT) and configuration.
            *   `crud/`: Create, Read, Update, Delete (CRUD) database operations.
            *   `db/`: Database session management and base model definitions.
            *   `models/`: SQLAlchemy database table models (e.g., `user.py`).
            *   `schemas/`: Pydantic data validation schemas (e.g., `user.py`).
        *   `.env`: Local environment variables for the backend.
        *   `Dockerfile`: Instructions to build the backend Docker image.
        *   `requirements.txt`: Python dependencies.
    *   `frontend/`: Contains the JavaScript React application (created with Vite).
        *   `src/`: The main application source code.
            *   `components/`: Reusable UI components (e.g., `SetupForm.tsx`, `LoginForm.tsx`).
            *   `context/`: React context providers (e.g., `AuthContext.tsx`).
            *   `pages/`: Top-level page components (e.g., `AuthPage.tsx`).
            *   `services/`: API communication logic (e.g., `api.ts`).
        *   `.env`: Local environment variables for the frontend.
        *   `Dockerfile`: Instructions to build the frontend Docker image.
        *   `tailwind.config.js` & `postcss.config.js`: Build configuration for Tailwind CSS.
    *   `docs/`: Project documentation.
        *   `troubleshooting.md`: A guide for solving common setup and runtime issues.
    *   `task_prompt/`: Contains the master prompt (`pms_master_task.md`) that guides the AI development process.
    *   `docker-compose.yml`: The central file for orchestrating all services.
    *   `.gitignore`: Files and directories to be ignored by version control.

---

#### 3. Configuration & Setup

The application is fully containerized using Docker and orchestrated with Docker Compose.

*   **`docker-compose.yml`:**
    *   Defines three services: `db` (PostgreSQL), `backend` (FastAPI), and `frontend` (React).
    *   Includes a `test` service for running the backend test suite in an isolated environment.
    *   Uses a custom bridge network `pms_network` to allow services to communicate using their service names (e.g., the backend connects to the database at `db:5432`).
    *   Exposes ports to the host machine: `5432` for the database, `8000` for the backend, and `3000` for the frontend.
    *   Uses `env_file` to inject environment variables into the backend and database containers.

*   **Backend Configuration (`backend/.env`):**
    *   `DATABASE_URL`: The full connection string for SQLAlchemy to connect to the PostgreSQL database.
    *   `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`: Settings for JWT generation and validation.
    *   `CORS_ORIGINS`: A comma-separated list of URLs that the backend will accept requests from. This is crucial for allowing the frontend (running in the browser) to communicate with the backend.

*   **Frontend Configuration (`frontend/.env`):**
    *   The frontend uses a **Vite proxy** for API requests in the development environment. This means no `.env` file or `VITE_API_BASE_URL` variable is required for local development, as all requests to `/api` are automatically forwarded to the backend service.

---

#### 4. Feature Implementation: Initial Setup
*   **Database Schema Management:** The project uses **Alembic** for database schema migrations. On startup, the `docker-compose.yml` configuration automatically runs `alembic upgrade head` to ensure the database schema is up-to-date with the latest versioned migration scripts. The old `create_all` mechanism has been removed.
*   **Backend Logic (`/api/v1/auth/status` & `/api/v1/auth/setup`):**
    *   The `GET /status` endpoint checks if any users exist in the database.
    *   The `POST /setup` endpoint allows the creation of the *first* user only. It validates the incoming data using the `UserCreate` Pydantic schema, which includes strong password validation rules (length, uppercase, lowercase, number, special character). If validation passes, it hashes the password and saves the new admin user to the database.

*   **Frontend Logic (`AuthPage.tsx` & `SetupForm.tsx`):**
    *   The `AuthPage` component first calls the `/status` endpoint.
    *   If `setup_needed` is `true`, it renders the `SetupForm` component.
    *   The `SetupForm` handles user input for name, email, and password. On submission, it sends a `POST` request to the `/setup` endpoint.
    *   It correctly handles and displays validation errors returned from the backend (e.g., "Password must be at least 8 characters long").
    *   Upon successful setup, the `onSuccess` callback is triggered, which will cause the `AuthPage` to re-check the status and then render the `LoginForm` (to be implemented next).

---

#### 5. How to Run the Project

1.  **Ensure Docker and Docker Compose are installed.**
2.  **Configure Environment Files:**
    *   **Backend:** Create a file at `backend/.env`. You can copy `backend/.env.example` as a template. The default values are suitable for local development and include the correct `CORS_ORIGINS` for the frontend service (`http://localhost:3000`).
    *   **Frontend:** No `.env` file is needed for local development due to the Vite proxy setup.
4.  **Run the application** from the project's root directory:
    ```bash
    docker-compose up --build db backend frontend
    ```
5.  **Access the services:**
    *   Frontend: `http://localhost:3000`
    *   Backend API Docs: `http://localhost:8000/docs`

---

#### 6. How to Run Tests

1.  **Run the backend tests** from the project's root directory:
    ```bash
    docker-compose run --rm test
    ```
2.  This command starts a dedicated test container, runs `pytest` against an in-memory SQLite database, and then removes the container. This ensures tests are fast, isolated, and do not affect the development database.
3.  **Run the frontend tests** from the project's root directory:
    ```bash
    docker-compose run --rm frontend npm test
    ```
---

#### 7. Next Steps

The application is now stable and has a consistent UI. The next logical step is to begin planning for the next major feature from the requirements backlog.

1.  **Advanced Goal Planning & Tracking (FR13):** Allow users to define financial goals and track their progress.
2.  **Advanced Analytics (FR6):** Implement calculations for XIRR, Sharpe Ratio, and other performance metrics.
3.  **Data Import (FR7):** Implement the functionality to import transactions from broker statements.
