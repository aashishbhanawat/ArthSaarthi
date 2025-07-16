# Troubleshooting Guide

This document lists common issues encountered during setup and development, along with their solutions.

## 1. Docker: "no space left on device"

*   **Symptom:** Docker commands fail with a message about disk space.
*   **Cause:** An accumulation of old, unused Docker images, containers, and volumes.
*   **Solution:** Run Docker's built-in prune command to clean up unused resources.
    ```bash
    docker system prune -a
    ```

## 2. Docker Compose: "variable is not set" or "Database is uninitialized"

*   **Symptom:** `docker-compose up` shows warnings that environment variables are not set, and the PostgreSQL container fails to start.
*   **Cause:** Docker Compose is not correctly loading the `.env` file for variable substitution.
*   **Solution:** Ensure your `docker-compose.yml` file uses the `env_file` directive for each service that needs variables from the `.env` file. This explicitly tells Docker Compose where to find the file.

## 3. Backend: Pydantic `ValidationError` on startup

*   **Symptom:** The FastAPI application fails to start with a `ValidationError` about "Extra inputs are not permitted".
*   **Cause:** The Pydantic `Settings` class is configured to load the `.env` file directly (`env_file = ".env"`), but the file contains variables not defined in the class (like `POSTGRES_USER`).
*   **Solution:** Remove the `env_file` setting from the Pydantic `Settings.Config` class. Let Docker Compose handle injecting environment variables, and Pydantic will automatically read them from the container's environment.

## 4. Backend: `AttributeError` or `ModuleNotFoundError` for local modules

*   **Symptom:** The application fails with errors like `AttributeError: module 'app.schemas' has no attribute 'User'` or `ModuleNotFoundError`.
*   **Cause:** Incorrect Python import paths (e.g., `from .. import schemas`) or missing `__init__.py` files in directories.
*   **Solution:**
    1.  Ensure every directory within the `app/` folder contains an empty `__init__.py` file to mark it as a Python package.
    2.  Use absolute imports from the root of the application (e.g., `from app.schemas import user as user_schema`).

## 5. Backend: Missing Dependencies (`ModuleNotFoundError`)

*   **Symptom:** The backend fails to start, complaining about a missing module like `email-validator` or `python-multipart`.
*   **Cause:** A library we are using (e.g., Pydantic, FastAPI) has optional dependencies that are required for specific features (like email validation or form parsing) but are not installed by default.
*   **Solution:** Add the missing library to the `backend/requirements.txt` file and rebuild the Docker container (`docker-compose up --build`).

## 6. Frontend: CORS Errors or `ECONNREFUSED`

*   **Symptom:** The browser console shows a CORS error or a "Connection Refused" network error when the frontend tries to call the backend.
*   **Cause:** The backend is not configured to accept requests from the frontend's origin (URL), or the frontend is trying to call an incorrect backend address.
*   **Solution:** Use the CORS (Cross-Origin Resource Sharing) pattern.
    1.  In `backend/app/main.py`, implement the `CORSMiddleware` and configure it to read allowed origins from `settings.CORS_ORIGINS`.
    2.  In `backend/.env`, define the `CORS_ORIGINS` variable with a comma-separated list of all URLs the frontend might be accessed from (e.g., `http://localhost:3000,http://127.0.0.1:3000`).
    3.  In `frontend/src/services/api.ts`, ensure the `baseURL` points directly to the backend's exposed address (e.g., `http://localhost:8000/api/v1`).

## 7. Frontend: React crashes with "Objects are not valid as a React child"
*   **Symptom:** The application crashes when trying to display an error message from the backend.
*   **Cause:** The backend sends a detailed error object (e.g., `{"detail": [{"msg": "Error message"}]}`), but the React code attempts to render this object directly instead of extracting the message string.
*   **Solution:** In the frontend's `catch` block for an API call, specifically parse the error response to extract the desired string message (e.g., `error.response?.data?.detail[0]?.msg`) before setting it in the state.

## 8. Backend: `psycopg2.OperationalError: Connection refused` on Startup

*   **Symptom:** The `backend` service fails to start with an error indicating it cannot connect to the `db` service, even with `depends_on` in `docker-compose.yml`.
*   **Cause:** This is a race condition. The `backend` container starts before the PostgreSQL server inside the `db` container is fully initialized and ready to accept connections.
*   **Solution:** Use a `healthcheck` in the `db` service in `docker-compose.yml`. This makes the `backend` service wait until the database is not just started, but actually healthy and ready for connections.
    ```yaml
    # In docker-compose.yml
    depends_on:
      db:
        condition: service_healthy
    ```

## 9. Backend: `AttributeError: module 'bcrypt' has no attribute '__about__'`
*   **Symptom:** The `backend` service fails to start with an `AttributeError` from `passlib` related to `bcrypt`.
*   **Cause:** A version mismatch between the `passlib` and `bcrypt` libraries.
*   **Solution:** Pin the `bcrypt` version to a known compatible version in `backend/requirements.txt`. For example: `bcrypt==3.2.2`. Then, rebuild the backend container (`docker-compose build backend`).

## Frontend Testing

1.  **Jest Configuration Errors:** If you encounter errors related to `import.meta` or other syntax issues when running frontend tests, ensure that the Babel configuration in `jest.config.js` is correctly set up to transform Vite-specific syntax. Refer to the configuration section in this document for the correct settings.
