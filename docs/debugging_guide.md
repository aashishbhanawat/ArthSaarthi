# Debugging Guide

This document outlines how to enable dynamic debug logging for different parts of the application. This is useful for troubleshooting issues without having to add temporary `print` or `console.log` statements.

## Backend Debugging

The backend uses a `DEBUG` flag to control verbose logging in the API endpoints.

**How to enable:**

1.  Open your `docker-compose.yml` or `docker-compose.override.yml` file.
2.  In the `environment` section for the `backend` service, add the following line:
    ```yaml
    - DEBUG=True
    ```
3.  Restart the backend container: `docker-compose up -d --build backend`.

When enabled, you will see detailed logs in the backend container's output for events like portfolio creation and transaction requests.

### Checking the Database Configuration

To debug database-related issues, it's useful to know which database the application is configured to use.

1.  **Check the `DATABASE_TYPE` variable:** In your `docker-compose.yml` or override files, check the `environment` section for the `backend` service. The `DATABASE_TYPE` variable can be set to `postgres` (default) or `sqlite`.
2.  **Check the startup logs:** When the backend container starts, the `entrypoint.sh` script will log which database it is initializing.
    *   For PostgreSQL: `Database type is PostgreSQL, applying Alembic migrations...`
    *   For SQLite: `Database type is SQLite, initializing database...`

## Frontend Debugging

The frontend uses a Vite environment variable `VITE_DEBUG_ENABLED` to control logging in the browser console.

**How to enable:**

1.  Create or open the `frontend/.env.local` file.
2.  Add the following line:
    ```
    VITE_DEBUG_ENABLED=true
    ```
3.  The Vite dev server will automatically pick up the change.