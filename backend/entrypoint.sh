#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Conditionally apply database migrations or create schema
if [ "$DATABASE_TYPE" = "sqlite" ]; then
  echo "Database type is SQLite. Creating schema from models..."
  python -m app.cli init-db --create-tables
else
  echo "Database type is PostgreSQL. Applying Alembic migrations..."
  alembic upgrade head
  echo "Seeding historical interest rates..."
  python -m app.cli init-db --no-create-tables
fi

# Seed the asset master data from the external source.
if [ "$ENVIRONMENT" != "test" ]; then
  echo "--- Seeding Asset Master Data ---"
  python -m app.cli seed-assets
else
  echo "--- Skipping Asset Seeding in Test Environment ---"
fi

# Start the application using exec to replace the shell process with the uvicorn process
echo "Starting Uvicorn server..."
# The --host 0.0.0.0 is important to make the server accessible from outside the container
# The "$@" allows passing additional arguments to the uvicorn command
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
