#!/bin/bash

echo "Cleaning project of temporary files and artifacts..."

# Stop and remove Docker containers to release any file locks
echo "Stopping Docker containers..."
docker-compose down

# Find and remove Python cache files/dirs
echo "Removing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +
find . -type d -name ".mypy_cache" -exec rm -rf {} +
find . -type f -name "*.pyc" -exec rm -f {} +
find . -type f -name "*.pyo" -exec rm -f {} +

# Find and remove build artifacts
echo "Removing build artifacts..."
find . -type d -name "build" -exec rm -rf {} +
find . -type d -name "dist" -exec rm -rf {} +
find . -type d -name "*.egg-info" -exec rm -rf {} +

# Find and remove test artifacts
echo "Removing test artifacts..."
find . -type f -name ".coverage" -exec rm -f {} +
rm -rf frontend/coverage
rm -rf playwright-report/
rm -rf test-results/
rm -f e2e/tests/temp_transactions.csv

# Find and remove frontend artifacts and node_modules
echo "Removing frontend artifacts and node_modules..."
rm -rf frontend/dist
rm -rf .cache/
rm -rf node_modules/
rm -rf frontend/node_modules/
rm -rf e2e/node_modules/

# Find and remove log files and temp docs
echo "Removing logs and temporary files..."
rm -rf backend/temp_seed_data/
find . -type f -name "npm-debug.log*" -exec rm -f {} +
find . -type f -name "yarn-debug.log*" -exec rm -f {} +
find . -type f -name "yarn-error.log*" -exec rm -f {} +
rm -f log.txt
rm -f docs/bug_reports_temp.md

echo "Project cleaned successfully."