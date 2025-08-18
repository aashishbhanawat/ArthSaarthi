#!/bin/bash

# This script is a unified, configurable local test runner for the ArthSaarthi project.
# It replicates all CI test scenarios (lint, unit, e2e) for both SQLite and PostgreSQL
# backends without requiring Docker.

set -e

# --- Configuration ---
DB_TYPE="sqlite"
TEST_SUITE="all"

DEFAULT_BACKEND_PORT=8008
DEFAULT_FRONTEND_PORT=3008
DEFAULT_POSTGRES_USER="postgres"
DEFAULT_POSTGRES_DB="postgres"
TEST_DB_NAME="arthsaarthi_test"

# --- PIDs for background processes ---
BACKEND_PID=""
FRONTEND_PID=""

# --- Helper Functions for colored output ---
print_info() { echo -e "\033[34m[INFO]\033[0m $1"; }
print_success() { echo -e "\033[32m[SUCCESS]\033[0m $1"; }
print_error() { echo -e "\033[31m[ERROR]\033[0m $1" >&2; }

show_help() {
cat << EOF
Usage: ./run_local_tests.sh [TEST_SUITE] [--db DB_TYPE]

Run the ArthSaarthi test suite locally without Docker.

TEST_SUITE:
  all         (Default) Runs linting, all unit tests, and all e2e tests.
  lint        Runs backend (ruff) and frontend (eslint) linters.
  backend     Runs backend (pytest) unit and integration tests.
  frontend    Runs frontend (jest) unit tests.
  e2e         Runs end-to-end (playwright) tests.

OPTIONS:
  --db <type> Specifies the database backend to use. Default is 'sqlite'.
              - sqlite: Uses a temporary file-based database. No external services needed.
              - postgres: Uses a local PostgreSQL and Redis server.
  -h, --help  Show this help message.
EOF
}

# --- Argument Parser ---
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -h|--help) show_help; exit 0 ;;
        --db) DB_TYPE="$2"; shift ;;
        lint|backend|frontend|e2e|all) TEST_SUITE=$1 ;;
        *) echo "Unknown parameter passed: $1"; show_help; exit 1 ;;
    esac
    shift
done

# --- Prerequisite Checks ---
check_prereqs() {
    print_info "Checking prerequisites for selected configuration..."
    if ! command -v python3 &> /dev/null || ! command -v pip &> /dev/null; then
        print_error "python3 and/or pip are not found. Please install Python 3.8+. See docs/testing_strategy.md for instructions."; exit 1
    fi
    if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
        print_error "node and/or npm are not found. Please install Node.js 18+. See docs/testing_strategy.md for instructions."; exit 1
    fi

    if [ "$DB_TYPE" == "postgres" ]; then
        if ! command -v psql &> /dev/null; then
            print_error "psql command not found. Please install the PostgreSQL client. See docs/testing_strategy.md for instructions."; exit 1
        fi
        if ! pg_isready -q -U "$DEFAULT_POSTGRES_USER"; then
            print_error "PostgreSQL server is not running or is not accessible for user '$DEFAULT_POSTGRES_USER'."; exit 1
        fi
        if ! command -v redis-cli &> /dev/null; then
            print_error "redis-cli command not found. Please install Redis. See docs/testing_strategy.md for instructions."; exit 1
        fi
        if ! redis-cli ping &> /dev/null; then
            print_error "Cannot connect to Redis server. Please ensure it is running."; exit 1
        fi
    fi
    print_success "Prerequisites met."
}

# --- Cleanup Function ---
cleanup() {
  print_info "Cleaning up background services and created files..."
  if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID 2>/dev/null || print_info "Backend server was not running."
  fi
  if [ -n "$FRONTEND_PID" ]; then
    kill $FRONTEND_PID 2>/dev/null || print_info "Frontend server was not running."
  fi

  rm -f backend/.env.test.local
  if [ "$DB_TYPE" == "sqlite" ]; then
    rm -f backend/test.db
  elif [ "$DB_TYPE" == "postgres" ]; then
    print_info "Dropping test database '$TEST_DB_NAME'..."
    PGPASSWORD=${POSTGRES_PASSWORD:-} psql -h localhost -U "$DEFAULT_POSTGRES_USER" -d "$DEFAULT_POSTGRES_DB" -c "DROP DATABASE IF EXISTS $TEST_DB_NAME;" > /dev/null
  fi
  print_success "Cleanup complete."
}
trap cleanup EXIT

# --- Test Functions ---

install_deps() {
    print_info "Installing all project dependencies..."
    pip install -r backend/requirements-dev.in > /dev/null 2>&1
    (cd frontend && npm install > /dev/null 2>&1)
    (cd e2e && npx playwright install --with-deps > /dev/null 2>&1)
    print_success "All dependencies installed."
}

run_lint() {
    print_info "--- Running Linters ---"
    (cd backend && ruff check .) && print_success "Backend linting passed."
    (cd frontend && npm run lint) && print_success "Frontend linting passed."
}

run_frontend_tests() {
    print_info "--- Running Frontend Unit Tests ---"
    (cd frontend && npm test)
    print_success "Frontend tests passed."
}

create_env_file() {
    local backend_port=$1
    local frontend_port=$2

    if [ "$DB_TYPE" == "sqlite" ]; then
        cat > backend/.env.test.local << EOF
SECRET_KEY=dummy-secret-key-for-testing
DATABASE_URL=sqlite:///./test.db
ENVIRONMENT=test
CORS_ORIGINS=http://localhost:$frontend_port,http://127.0.0.1:$frontend_port
PYTHONPATH=/app
DEPLOYMENT_MODE=desktop
DATABASE_TYPE=sqlite
CACHE_TYPE=disk
TESTING=True
EOF
    elif [ "$DB_TYPE" == "postgres" ]; then
        print_info "Creating test database '$TEST_DB_NAME'..."
        PGPASSWORD=${POSTGRES_PASSWORD:-} psql -h localhost -U "$DEFAULT_POSTGRES_USER" -d "$DEFAULT_POSTGRES_DB" -c "DROP DATABASE IF EXISTS $TEST_DB_NAME;" > /dev/null
        PGPASSWORD=${POSTGRES_PASSWORD:-} psql -h localhost -U "$DEFAULT_POSTGRES_USER" -d "$DEFAULT_POSTGRES_DB" -c "CREATE DATABASE $TEST_DB_NAME;" > /dev/null
        print_success "Test database created."

        cat > backend/.env.test.local << EOF
SECRET_KEY=dummy-secret-key-for-testing
DATABASE_URL=postgresql://${POSTGRES_USER:-$DEFAULT_POSTGRES_USER}:${POSTGRES_PASSWORD:-}@localhost:5432/$TEST_DB_NAME
REDIS_URL=redis://localhost:6379
ENVIRONMENT=test
CORS_ORIGINS=http://localhost:$frontend_port,http://127.0.0.1:$frontend_port
PYTHONPATH=/app
DATABASE_TYPE=postgres
CACHE_TYPE=redis
TESTING=True
EOF
    fi
    print_success "Created .env.test.local for $DB_TYPE backend."
}

run_backend_tests() {
    print_info "--- Running Backend Tests (DB: $DB_TYPE) ---"
    create_env_file 0 0 # Ports not needed for backend-only tests
    (cd backend && python -m dotenv -f .env.test.local run -- pytest -v)
    print_success "Backend tests passed."
}

find_free_port() {
  local port=$1
  while (lsof -i:$port > /dev/null); do
    port=$((port + 1))
  done
  echo $port
}

run_e2e_tests() {
    print_info "--- Running E2E Tests (DB: $DB_TYPE) ---"

    local backend_port=$(find_free_port $DEFAULT_BACKEND_PORT)
    local frontend_port=$(find_free_port $DEFAULT_FRONTEND_PORT)
    print_info "Using Backend Port: $backend_port, Frontend Port: $frontend_port"

    create_env_file $backend_port $frontend_port

    print_info "Starting backend server..."
    (cd backend && python -m dotenv -f .env.test.local run -- uvicorn app.main:app --host 0.0.0.0 --port $backend_port) &
    BACKEND_PID=$!
    print_info "Waiting for backend to be ready..."
    timeout 60s bash -c "until curl -s -f http://localhost:$backend_port/api/v1/auth/status > /dev/null; do sleep 1; done"
    print_success "Backend is up."

    print_info "Starting frontend server..."
    (cd frontend && npm run dev -- --port $frontend_port) &
    FRONTEND_PID=$!
    print_info "Waiting for frontend to be ready..."
    timeout 60s bash -c "until curl -s -f http://localhost:$frontend_port > /dev/null; do sleep 1; done"
    print_success "Frontend is up."

    print_info "Running Playwright E2E tests..."
    export E2E_BASE_URL="http://localhost:$frontend_port"
    (cd e2e && npx playwright test)
    print_success "E2E tests passed."
}

# --- Main Execution Logic ---

main() {
    check_prereqs
    install_deps

    case $TEST_SUITE in
        all)
            run_lint
            run_frontend_tests
            run_backend_tests
            run_e2e_tests
            ;;
        lint)
            run_lint
            ;;
        backend)
            run_backend_tests
            ;;
        frontend)
            run_frontend_tests
            ;;
        e2e)
            run_e2e_tests
            ;;
    esac

    print_success "\n✅ All selected tests passed successfully for the '$DB_TYPE' configuration!"
}

main

exit 0