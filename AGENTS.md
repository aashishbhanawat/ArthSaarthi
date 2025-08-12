# Guide for AI Assistants

This guide provides instructions for setting up a local development and testing environment that is self-contained and does not require Docker or external services like a running PostgreSQL server.

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
Use `create_file_with_block` with the following content:
```
# frontend/.env.local
VITE_API_PROXY_TARGET=http://localhost:8000
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
(cd backend && python -m dotenv -f .env.test run -- pytest -v)

# Frontend Tests
(cd frontend && npm test)
```

### 2.3. End-to-End (E2E) Tests

This requires running the backend and frontend servers in separate processes.

**Terminal 1: Start Backend Server (for E2E)**
```bash
(cd backend && python -m dotenv -f .env.test run -- uvicorn app.main:app --host 127.0.0.1 --port 8000)
```

**Terminal 2: Start Frontend Server (for E2E)**
```bash
(cd frontend && npm run dev)
```

**Terminal 3: Run E2E Tests**
```bash
(cd e2e && npx playwright test)
```

After running the tests, you can kill the background server processes.
