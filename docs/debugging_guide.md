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

## Background Job Scheduler Troubleshooting

The background job scheduler runs tasks asynchronously via APScheduler.

### 1. Checking Scheduler Status & Logs via UI
1. Navigate to **Admin -> System Maintenance** in the application.
2. Locate the **Background Job Scheduler** card.
3. Check the status badge (`APScheduler Active` vs `Stopped`) and next run timestamps.
4. Click **Execution Logs** to view recent execution records, durations, and any captured error tracebacks.

### 2. Inspecting Logs in the Database
To view recorded job executions directly from the database:
```sql
SELECT job_id, job_name, status, execution_time_seconds, error_message, created_at
FROM scheduled_job_logs
ORDER BY created_at DESC
LIMIT 20;
```

### 3. Common Issues & Solutions
* **Job Stuck in RUNNING Status:**
  If a server crash occurs while a job is running, restart the backend container or process. The in-memory execution set will reset, and the scheduler will resume normal operation.
* **409 Conflict when Triggering Job Manually:**
  Indicates the requested job is currently executing. Wait for the active execution to complete before triggering another run.
* **Database Locked (SQLite):**
  Ensure long-running tasks don't hold open write transactions. Tasks must use isolated scoped sessions (`SessionLocal()`) and commit promptly.
