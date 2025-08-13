# Guide for AI Assistants

This guide provides instructions for setting up a local development and testing environment that is self-contained and does not require Docker or external services like a running PostgreSQL server.

## 0. Prerequisites

This environment requires a Redis server for caching.

### Install Redis
On Debian-based systems (like Ubuntu), you can install Redis with:
```bash
sudo apt-get update && sudo apt-get install -y redis-server
```

## 1. Initial Environment Setup

This only needs to be done once.

### 1.1. Install Dependencies

Install all Python and Node.js dependencies for the backend, frontend, and E2E tests.

```bash
pip install -r backend/requirements.txt -r backend/requirements-dev.in
cd frontend && npm install && cd ..
cd e2e && npm install && cd ..
```

### 1.2. Configure Environment Files

Create the necessary environment files using the `create_file_with_block` tool. This is more reliable than copying and overwriting.

**1. Create `backend/.env`**
Use `create_file_with_block` with the following content:
```
# backend/.env
SECRET_KEY=dummy-secret-key-for-dev
DATABASE_URL=sqlite:///./dev.db
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://localhost,http://127.0.0.1
```

**2. Create `backend/.env.test`**
Use `create_file_with_block` with the following content:
```
# backend/.env.test
SECRET_KEY=dummy-secret-key-for-testing
DATABASE_URL=sqlite:///./test.db
REDIS_URL=redis://localhost:6379/1
ENVIRONMENT=test
CORS_ORIGINS=http://localhost:3000,http://localhost,http://127.0.0.1
```

**3. Create `frontend/.env.local`**
Use `create_file_with_block` with the following content. This configures the frontend to proxy API requests to the local backend and to bind the server to the local interface.
```
# frontend/.env.local
VITE_API_PROXY_TARGET=http://localhost:8001
VITE_DEV_SERVER_HOST=127.0.0.1
```

## 2. Running All Checks

This is the main command to run all linters and tests. It uses the SQLite database for backend and E2E tests, which should now pass in this environment.

### 2.1. Linting

```bash
# Backend Linter
(cd backend && ruff check .)

# Frontend Linter
(cd frontend && npm run lint)
```

### 2.2. Unit & Integration Tests

The backend tests will use the `test.db` SQLite database file. The frontend tests are self-contained.

```bash
# Backend Tests
# To run with SQLite (recommended for sandboxed environments):
(cd backend && FORCE_SQLITE_TEST=true python -m dotenv -f .env.test run -- pytest -v)

# To run with PostgreSQL (for local development):
# - Ensure your `.env.test` file has the correct `DATABASE_URL` for your PostgreSQL instance.
(cd backend && python -m dotenv -f .env.test run -- pytest -v)

# Frontend Tests
(cd frontend && npm test)
```

### 2.3. End-to-End (E2E) Tests

This requires running the backend and frontend servers in separate processes.

**Important**: Before running E2E tests, ensure you have a clean database.
```bash
rm -f backend/test.db
```

**Terminal 1: Start Redis Server**
Ensure the Redis server is running before starting the backend.
```bash
# This command might require sudo
sudo service redis-server start
```

**Note on ports**: The default ports are 8001 for the backend and 3000 for the frontend. If these ports are in use on your system, you can change them. For example, to use port 8002 for the backend and 3001 for the frontend, you would need to:
1.  Update `CORS_ORIGINS` in `backend/.env.test` to include `http://localhost:3001`.
2.  Start the backend server with the `--port 8002` flag.
3.  Update `VITE_API_PROXY_TARGET` in `frontend/.env.local` to `http://localhost:8002`.
4.  The `npm run dev` command in `frontend/package.json` needs to be updated to accept a port. Or you can run `(cd frontend && npm run dev -- --port 3001)`.
5.  Set the `E2E_BASE_URL` environment variable to `http://localhost:3001` before running the tests.

**Terminal 2: Start Backend Server (for E2E)**
```bash
(cd backend && python -m dotenv -f .env.test run -- uvicorn app.main:app --host 127.0.0.1 --port 8001) &
```

**Terminal 3: Start Frontend Server (for E2E)**
To ensure all environment variables are loaded correctly, especially when running in the background, source the `.env.local` file.
```bash
(cd frontend && export $(grep -v '^#' .env.local | xargs) && npm run dev) &
```

**Terminal 4: Run E2E Tests**
Set the `E2E_BASE_URL` for the Playwright tests to point to the local frontend server.
```bash
export E2E_BASE_URL='http://localhost:3000'
(cd e2e && npx playwright test)
```

After running the tests, you can kill the background server processes.
