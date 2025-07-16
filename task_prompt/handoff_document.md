### Project Handoff Document: Personal Portfolio Management System

#### 1. Project Goal & Current Status

*   **Goal:** To build a full-stack, containerized Personal Portfolio Management System (PMS).
*   **Current Status:** The initial "Core User Authentication" feature is **complete**. The system can successfully check if an admin user exists, allow the first user to register as an admin with a secure password, and is ready for the login functionality to be implemented. The frontend and backend are communicating successfully within the Docker environment and are accessible over the local network.
*   **Testing:** A full suite of automated backend tests (`pytest`) has been implemented for the authentication module, covering unit and integration tests. All tests are passing. A comprehensive set of automated frontend tests using Jest and React Testing Library has also been implemented for the LoginForm component. These tests cover rendering, user input, API calls, and error handling. All tests are passing.
*   **Implemented Functionalities:** The core user authentication module is now complete. This includes user registration, login, and basic session management. The system is able to verify if an admin user exists, allow the first user to register as an admin with a secure password, and authenticate subsequent users with login functionality.


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
    *   `VITE_API_BASE_URL`: The full base URL for the backend API. This must be the **host machine's LAN IP address** (e.g., `http://192.168.1.5:8000/api/v1`) to allow access from other devices on the network, not just `localhost`.

---

#### 4. Feature Implementation: Initial Setup

*   **Backend Logic (`/api/v1/auth/status` & `/api/v1/auth/setup`):**
    *   On startup (via FastAPI's `lifespan` event), the backend uses SQLAlchemy's `create_all` to initialize the database schema based on the `User` model. This is skipped in the test environment.
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
2.  **Find your host machine's LAN IP address** (e.g., `192.168.1.100`).
3.  **Configure Environment Files:**
    *   In `frontend/.env`, set `VITE_API_BASE_URL=http://<YOUR_HOST_IP>:8000/api/v1`.
    *   In `backend/.env`, add your frontend's network URL to `CORS_ORIGINS` (e.g., `CORS_ORIGINS=...,http://<YOUR_HOST_IP>:3000`).
4.  **Run the application** from the project's root directory:
    ```bash
    docker-compose up --build db backend frontend
    ```
5.  **Access the services:**
    *   Frontend: `http://<YOUR_HOST_IP>:3000`
    *   Backend API Docs: `http://<YOUR_HOST_IP>:8000/docs`

---

#### 6. How to Run Tests

The project includes a robust backend test suite.

1.  **Run the tests** from the project's root directory:
    ```bash
    docker-compose run --rm test
    ```
2.  This command starts a dedicated test container, runs `pytest` against an in-memory SQLite database, and then removes the container. This ensures tests are fast, isolated, and do not affect the development database.

---

#### 7. Next Steps

The foundation is solid and well-documented. The immediate next step is to continue with the **User Authentication** module.

The next module to be developed is **User Management**.

1.  **Define the User Management features and backend API endpoints:** This will involve backend development and database administration.
2.  **Design the User Management frontend components:** This will involve frontend development and UI/UX design.