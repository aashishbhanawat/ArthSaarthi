#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Conditionally initialize the database based on DATABASE_TYPE
if [ "$DATABASE_TYPE" = "sqlite" ]; then
  echo "E2E: Database type is SQLite, initializing database..."
  python -m app.cli init-db
else
  # Function to check if the test database exists
  ensure_test_db() {
      echo "E2E: Ensuring test database exists..."
      # The python script will exit with a non-zero status if it fails
      python -c "from app.db.session import SessionLocal; from sqlalchemy import text; db = SessionLocal(); db.execute(text('SELECT 1')); db.close()"
  }

  # Wait for the database to be ready
  # Retry logic to handle initial connection errors
  n=0
  until [ $n -ge 10 ]
  do
      ensure_test_db && break
      n=$[$n+1]
      sleep 5
  done

  # Run database migrations
  echo "E2E: Applying database migrations..."
  alembic upgrade head
fi

# Start the application using a Uvicorn server suitable for E2E testing
echo "E2E: Starting Uvicorn server for E2E tests..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app