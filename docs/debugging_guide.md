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

## Frontend Debugging

The frontend uses a Vite environment variable `VITE_DEBUG_ENABLED` to control logging in the browser console.

**How to enable:**

1.  Create or open the `frontend/.env.local` file.
2.  Add the following line:
    ```
    VITE_DEBUG_ENABLED=true
    ```
3.  The Vite dev server will automatically pick up the change.