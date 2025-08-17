#!/bin/bash

# This script automates the local E2E test setup without Docker.
# It installs dependencies, sets up a clean environment with SQLite,
# finds free ports, starts services, runs tests, and cleans up.

set -e

# --- Default Ports ---
DEFAULT_BACKEND_PORT=8008
DEFAULT_FRONTEND_PORT=3008
DEFAULT_REDIS_PORT=6379

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


# --- Cleanup Function ---
function cleanup() {
  print_info "Cleaning up background services and created files..."

  # Remove created environment files
  print_info "Removing temporary environment files..."
  rm -f backend/.env.test
  rm -f backend/test.db # Remove the SQLite test database

  print_success "Cleanup complete."
}

# Register the cleanup function to be called on script exit, error, or interrupt
trap cleanup EXIT

# --- Step 1: Install Dependencies ---
print_info "Installing dependencies..."
pip install -r backend/requirements.txt -r backend/requirements-dev.in > /dev/null 2>&1
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
PYTHONPATH=/app
DEPLOYMENT_MODE=desktop
DATABASE_TYPE=sqlite
CACHE_TYPE=disk
TESTING=True
EOF

print_success "Environment files created."

# --- Step 3: Run Backend Tests in Desktop Mode ---
print_info "Running Backend Tests in Desktop Mode..."
(cd backend && FORCE_SQLITE_TEST=true python -m dotenv -f .env.test run -- pytest -v)

print_success "Backend Tests in Desktop Mode finished successfully."

# The 'trap cleanup EXIT' will handle the cleanup automatically.
exit 0
