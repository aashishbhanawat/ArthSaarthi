#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Apply database migrations
echo "Applying database migrations..."
alembic upgrade head

# Seed the database with master asset data.
# This is idempotent and safe to run on every startup.
echo "Seeding initial asset data..."
python -m app.cli seed-assets

# Start the application using exec to replace the shell process with the uvicorn process
echo "Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug