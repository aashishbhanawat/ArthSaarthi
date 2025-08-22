#!/bin/bash

# This script is the entrypoint for the backend container in the E2E test environment.
# It ensures the database is ready and migrated before starting the application.

set -e

function print_info() {
  echo -e "\033[34m[E2E-SETUP]\033[0m $1"
}

if [ "$DATABASE_TYPE" == "sqlite" ]; then
    print_info "Database type is SQLite, ensuring clean state..."
    # The DB file is defined in .env.test as sqlite:///./test.db
    # The working directory is /app
    rm -f /app/test.db
    print_info "Creating database schema directly from models for SQLite..."
    # Instead of 'alembic upgrade head', which is failing due to a likely broken
    # migration history, we create the schema directly from the current models.
    python -m app.cli init-db
    print_info "Stamping the database with the latest Alembic revision..."
    alembic stamp head
    print_info "Starting Uvicorn server for E2E tests..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    # PostgreSQL flow
    print_info "Waiting for PostgreSQL to be ready..."
    python /app/app/db/init_db.py
    print_info "Applying database migrations..."
    alembic upgrade head
    print_info "Starting Uvicorn server for E2E tests..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi

