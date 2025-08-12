#!/bin/bash
cd "$(dirname "$0")"

# Exit immediately if a command exits with a non-zero status.
set -e

# Ensure the test database exists before proceeding.
# The python script has a built-in retry mechanism.
echo "Ensuring test database exists..."
python -m app.db.init_db

# Now that the DB is guaranteed to exist, run the original entrypoint logic
echo "Applying database migrations..."
alembic upgrade head

echo "Starting Uvicorn server for E2E tests..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8002