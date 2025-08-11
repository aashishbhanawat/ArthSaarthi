#!/bin/bash

# This script builds a standalone, one-click executable for the application.
# It packages the frontend and backend together using PyInstaller.

# --- Helper Functions ---
function print_info() {
    echo -e "\033[34m[INFO]\033[0m $1"
}

function print_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

function print_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
    exit 1
}

# --- Start of Build Process ---
print_info "Starting build process for packaged application..."

# Ensure we are in the root directory of the project
if [ ! -f "README.md" ]; then
    print_error "This script must be run from the root directory of the project."
fi

# 1. Build the frontend
print_info "Building the frontend..."
cd frontend || print_error "Failed to navigate to frontend directory."
npm install || print_error "npm install failed."
npm run build || print_error "npm run build failed."
cd ..
print_success "Frontend built successfully."

# 2. Prepare backend for packaging
print_info "Preparing backend for packaging..."
BE_DIR="backend"
STATIC_DIR="$BE_DIR/static"
FRONTEND_DIST="frontend/dist"

# Create the directory for static assets inside the backend folder
rm -rf "$STATIC_DIR"
mkdir -p "$STATIC_DIR"

# Copy built frontend assets to the backend static directory
cp -r $FRONTEND_DIST/* "$STATIC_DIR/"
print_success "Frontend assets copied to $STATIC_DIR."

# 3. Run PyInstaller
print_info "Running PyInstaller..."
cd $BE_DIR || print_error "Failed to navigate to backend directory."

# Set environment variables for the build.
# SERVE_STATIC_FRONTEND=True tells the FastAPI app to serve the frontend.
# The database URL is not set, so it will default to the SQLite database.
export SERVE_STATIC_FRONTEND=True

pyinstaller \
    --name pms_app \
    --onefile \
    --windowed \
    --noconfirm \
    --add-data "static:static" \
    --add-data "alembic:alembic" \
    --add-data "alembic.ini:." \
    app/main.py

# Unset the env var
unset SERVE_STATIC_FRONTEND

cd ..
print_success "PyInstaller build complete. The executable can be found in backend/dist/."
print_info "Note: This script generates a Linux executable. For Windows/macOS, it must be run on those respective operating systems."
