# Guide for AI Assistants

This guide provides instructions for setting up a local development and testing environment that is self-contained and does not require Docker.

## 1. Running All Checks

This is the main command to run all linters and tests. It uses the SQLite database for backend and E2E tests.

### 1.1. Linting

```bash
# Backend Linter
(cd backend && ruff check .)

# Frontend Linter
(cd frontend && npm run lint)
```

### 1.2. Unit & Integration Tests

The backend tests will use an auto-generated `test.db` SQLite database file. The frontend tests are self-contained.

```bash
# Backend Tests
# To run with SQLite (recommended for sandboxed environments):
(cd backend && FORCE_SQLITE_TEST=true python -m dotenv -f .env.test run -- pytest -v)

# Frontend Tests
(cd frontend && npm test)
```

### 1.3. End-to-End (E2E) Tests

The E2E tests are run using a dedicated script that handles all setup, execution, and cleanup.

**Run E2E Test Suite**
This single command will:
1.  Install any missing prerequisites (like Redis).
2.  Install all project dependencies.
3.  Create the necessary test environment files.
4.  Start the backend, frontend, and Redis services on dynamically chosen ports.
5.  Run the complete Playwright E2E test suite.
6.  Clean up all running processes and temporary files automatically.

```bash
./run_e2e_local.sh
```

This is the definitive way to run E2E tests in a non-Dockerized environment.
