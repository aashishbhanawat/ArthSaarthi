#!/bin/bash
set -e

DB_TYPE="sqlite"
DEFAULT_BACKEND_PORT=8008
DEFAULT_FRONTEND_PORT=3008
BACKEND_PID=""
FRONTEND_PID=""

print_info() { echo -e "\033[34m[INFO]\033[0m $1"; }
print_success() { echo -e "\033[32m[SUCCESS]\033[0m $1"; }
print_error() { echo -e "\033[31m[ERROR]\033[0m $1" >&2; }

cleanup() {
  print_info "Cleaning up background services and created files..."
  if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID 2>/dev/null || print_info "Backend server was not running."
  fi
  if [ -n "$FRONTEND_PID" ]; then
    kill $FRONTEND_PID 2>/dev/null || print_info "Frontend server was not running."
  fi
  pkill -f "node /app/frontend/node_modules/.bin/vite" || true
  rm -f backend/.env.test
  rm -f frontend/.env.development.local
  rm -f backend/test.db
  print_success "Cleanup complete."
}
trap cleanup EXIT

create_env_file() {
    local backend_port=$1
    local frontend_port=$2
    cat > backend/.env.test << EOF
SECRET_KEY=dummy-secret-key-for-testing
DATABASE_URL=sqlite:///./test.db
ENVIRONMENT=test
CORS_ORIGINS=http://localhost:$frontend_port,http://127.0.0.1:$frontend_port
PYTHONPATH=.
DEPLOYMENT_MODE=server
DATABASE_TYPE=sqlite
CACHE_TYPE=disk
TESTING=True
EOF
    print_success "Created .env.test for $DB_TYPE backend."
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
    cat > frontend/.env.development.local << EOF
VITE_API_PROXY_TARGET=http://127.0.0.1:$backend_port
EOF
    print_info "Initializing database..."
    (cd backend && python -m dotenv -f .env.test run -- python -m app.cli init-db)
    print_success "Database initialized."
    print_info "Starting backend server..."
    (cd backend && uvicorn app.main:app --host 127.0.0.1 --port $backend_port --env-file .env.test) &
    BACKEND_PID=$!
    print_info "Waiting for backend to be ready..."
    timeout 60s bash -c "until curl -s -f http://127.0.0.1:$backend_port/api/v1/auth/status > /dev/null; do sleep 1; done"
    print_success "Backend is up."
    print_info "Starting frontend server..."
    (cd frontend && npm run dev -- --port $frontend_port) &
    FRONTEND_PID=$!
    print_info "Waiting for frontend to be ready..."
    timeout 60s bash -c "until curl -s -f http://127.0.0.1:$frontend_port > /dev/null; do sleep 1; done"
    print_success "Frontend is up."
    print_info "Running Playwright E2E tests..."
    export E2E_BASE_URL="http://127.0.0.1:$frontend_port"
    export E2E_BACKEND_URL="http://127.0.0.1:$backend_port"
    (cd e2e && xvfb-run --auto-servernum --server-args="-screen 0 1280x960x24" npx playwright test)
    print_success "E2E tests passed."
}

run_e2e_tests
