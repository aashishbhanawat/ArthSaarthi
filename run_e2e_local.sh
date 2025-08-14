#!/bin/bash

# This script automates the local E2E test setup without Docker.
# It installs dependencies, sets up a clean environment with SQLite,
# finds free ports, starts services, runs tests, and cleans up.

set -e

# --- Helper Functions for colored output ---
function print_info() {
  echo -e "\033[34m[INFO]\033[0m $1"
}

function print_success() {
  echo -e "\033[32m[SUCCESS]\033[0m $1"
}

function print_error() {
  echo -e "\033[31m[ERROR]\033[0m $1" >&2
}

# --- Default Port Definitions ---
DEFAULT_REDIS_PORT=6379
DEFAULT_BACKEND_PORT=8001
DEFAULT_FRONTEND_PORT=3000

# --- Variable Definitions ---
REDIS_PID=""
BACKEND_PID=""
FRONTEND_PID=""
NEW_REDIS_PORT=$DEFAULT_REDIS_PORT
NEW_BACKEND_PORT=$DEFAULT_BACKEND_PORT
NEW_FRONTEND_PORT=$DEFAULT_FRONTEND_PORT

# --- Cleanup Function ---
function cleanup() {
  print_info "Cleaning up background services and created files..."

  # Kill processes
  if [ -n "$FRONTEND_PID" ]; then
    print_info "Stopping frontend server (PID: $FRONTEND_PID)..."
    kill "$FRONTEND_PID" >/dev/null 2>&1 || print_error "Failed to stop frontend."
  fi
  if [ -n "$BACKEND_PID" ]; then
    print_info "Stopping backend server (PID: $BACKEND_PID)..."
    kill "$BACKEND_PID" >/dev/null 2>&1 || print_error "Failed to stop backend."
  fi
  if [ -n "$REDIS_PID" ]; then
    print_info "Stopping Redis server (PID: $REDIS_PID)..."
    kill "$REDIS_PID" >/dev/null 2>&1 || print_error "Failed to stop Redis."
  fi

  # Remove created environment files
  print_info "Removing temporary environment files..."
  rm -f backend/.env.test
  rm -f frontend/.env.local
  rm -f backend/test.db # Remove the SQLite test database

  print_success "Cleanup complete."
}

# Register the cleanup function to be called on script exit, error, or interrupt
trap cleanup EXIT

# --- Step 1: Check and Install Prerequisites ---
# Check for Redis and install if not present
if ! command -v redis-server &> /dev/null
then
    print_info "Redis server not found. Installing..."
    # Using sudo because this is a system-level package.
    # The execution environment must allow for this.
    sudo apt-get update > /dev/null 2>&1
    sudo apt-get install -y redis-server > /dev/null 2>&1
    print_success "Redis server installed."
else
    print_info "Redis server already installed."
fi

# --- Step 2: Install Dependencies ---
print_info "Installing dependencies..."
pip install -r backend/requirements.txt -r backend/requirements-dev.in > /dev/null 2>&1
(cd frontend && npm install > /dev/null 2>&1)
(cd e2e && npm install > /dev/null 2>&1)
print_success "All dependencies installed."

# --- Step 2: Create Environment Files ---
print_info "Creating clean environment files for testing..."

# Create backend/.env.test to use SQLite
cat > backend/.env.test << EOF
SECRET_KEY=dummy-secret-key-for-testing
DATABASE_URL=sqlite:///./test.db
REDIS_URL=redis://localhost:$DEFAULT_REDIS_PORT
ENVIRONMENT=test
CORS_ORIGINS=http://localhost:$DEFAULT_FRONTEND_PORT,http://127.0.0.1:$DEFAULT_FRONTEND_PORT
EOF

# Create frontend/.env.local to proxy to the local backend
cat > frontend/.env.local << EOF
VITE_API_PROXY_TARGET=http://localhost:$DEFAULT_BACKEND_PORT
VITE_DEV_SERVER_HOST=127.0.0.1
EOF

print_success "Environment files created."


# --- Step 3: Find and assign free ports ---
print_info "Checking for available ports..."

function find_free_port() {
  local port=$1
  while lsof -i:$port >/dev/null; do
    print_info "Port $port is in use. Trying next port..."
    port=$((port+1))
  done
  echo "$port"
}

NEW_REDIS_PORT=$(find_free_port "$DEFAULT_REDIS_PORT")
NEW_BACKEND_PORT=$(find_free_port "$DEFAULT_BACKEND_PORT")
NEW_FRONTEND_PORT=$(find_free_port "$DEFAULT_FRONTEND_PORT")
print_success "Assigned ports: Redis=$NEW_REDIS_PORT, Backend=$NEW_BACKEND_PORT, Frontend=$NEW_FRONTEND_PORT"


# --- Step 4: Update configuration files with dynamic ports ---
print_info "Updating configuration files with dynamic ports..."
sed -i "s/REDIS_URL=redis:\/\/localhost:$DEFAULT_REDIS_PORT/REDIS_URL=redis:\/\/localhost:$NEW_REDIS_PORT/" backend/.env.test
sed -i "s/VITE_API_PROXY_TARGET=http:\/\/localhost:$DEFAULT_BACKEND_PORT/VITE_API_PROXY_TARGET=http:\/\/localhost:$NEW_BACKEND_PORT/" frontend/.env.local
# Update CORS_ORIGINS for backend
CORS_ORIGINS="http://localhost:$NEW_FRONTEND_PORT,http://127.0.0.1:$NEW_FRONTEND_PORT"
sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=$CORS_ORIGINS|" backend/.env.test
print_success "Configuration updated."


# --- Step 5: Start Redis Server ---
print_info "Starting Redis server on port $NEW_REDIS_PORT..."
redis-server --port "$NEW_REDIS_PORT" --daemonize yes --logfile redis.log
# Since daemonize is used, we don't get a PID directly. We'll rely on cleanup to kill it by port/process name if needed.
# For simplicity in this script, we'll assume the trap-based cleanup is sufficient.
REDIS_PID=$(pgrep -f "redis-server.*:$NEW_REDIS_PORT")
if [ -z "$REDIS_PID" ]; then
    print_error "Failed to start Redis server. Check redis.log."
    exit 1
fi
print_info "Redis started with PID: $REDIS_PID"


# --- Step 6: Start Backend Server ---
print_info "Starting backend server on port $NEW_BACKEND_PORT..."
(cd backend && nohup python -m dotenv -f .env.test run -- uvicorn app.main:app --host 127.0.0.1 --port "$NEW_BACKEND_PORT" > ../backend.log 2>&1) &
BACKEND_PID=$!
print_info "Backend started with PID: $BACKEND_PID"


# --- Step 7: Start Frontend Server ---
print_info "Starting frontend development server on port $NEW_FRONTEND_PORT..."
(cd frontend && nohup npm run dev -- --port "$NEW_FRONTEND_PORT" > ../frontend.log 2>&1) &
FRONTEND_PID=$!
print_info "Frontend started with PID: $FRONTEND_PID"

# --- Step 8: Wait for Services to be Ready ---
print_info "Waiting for services to become available..."
TIMEOUT=120 # Increased timeout for slower CIs

# Wait for backend
BACKEND_HEALTH_URL="http://127.0.0.1:$NEW_BACKEND_PORT/api/v1/openapi.json"
print_info "Pinging backend at: $BACKEND_HEALTH_URL"
for ((i=1; i<=TIMEOUT; i++)); do
  if curl -s --fail "$BACKEND_HEALTH_URL" > /dev/null; then
    print_success "Backend is ready."
    break
  fi
  if [ $i -eq $TIMEOUT ]; then
    print_error "Backend failed to start within $TIMEOUT seconds."
    cat backend.log
    exit 1
  fi
  sleep 1
done

# Wait for frontend
FRONTEND_HEALTH_URL="http://127.0.0.1:$NEW_FRONTEND_PORT"
print_info "Pinging frontend at: $FRONTEND_HEALTH_URL"
for ((i=1; i<=TIMEOUT; i++)); do
  # Use curl with a timeout and retry mechanism
  if curl -s --head --fail --max-time 5 "$FRONTEND_HEALTH_URL" > /dev/null; then
    print_success "Frontend is ready."
    break
  fi
  if [ $i -eq $TIMEOUT ]; then
    print_error "Frontend failed to start within $TIMEOUT seconds."
    cat frontend.log
    exit 1
  fi
  sleep 1
done


# --- Step 9: Run E2E Tests ---
print_info "Running Playwright E2E tests..."
export E2E_BASE_URL="http://127.0.0.1:$NEW_FRONTEND_PORT"
(cd e2e && npx playwright test)

print_success "E2E tests finished successfully."

# The 'trap cleanup EXIT' will handle the cleanup automatically.
exit 0
