#!/bin/bash

# Native Setup Script for macOS
# This script automates the setup of the Personal Portfolio Management System on macOS.
# It assumes you have Homebrew installed.

# --- Helper Functions ---
function print_info() {
    echo -e "\033[34m[INFO]\033[0m $1"
}

function print_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

function print_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# --- Check for Homebrew ---
if ! command -v brew &> /dev/null; then
    print_error "Homebrew not found. Please install it from https://brew.sh/"
    exit 1
fi

# --- Main Setup ---
print_info "Starting native setup for macOS..."

# Update Homebrew
print_info "Updating Homebrew..."
brew update

# Install Dependencies
print_info "Installing dependencies: Python@3.11, Node@18, PostgreSQL@13, Redis..."
brew install python@3.11 node@18 postgresql@13 redis

# Start Services
print_info "Starting PostgreSQL and Redis services..."
brew services start postgresql@13
brew services start redis

print_success "All dependencies installed and services started."

# --- Manual Steps ---
echo ""
print_info "Next steps are manual:"
echo "1. Clone the project repository if you haven't already."
echo "   git clone <repository-url>"
echo "   cd personal-portfolio-management-system"
echo ""
echo "2. Configure the backend environment:"
echo "   cd backend"
echo "   cp .env.prod.example .env"
echo "   - Edit the '.env' file:"
echo "   - Set POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB."
echo "   - Generate and set a SECRET_KEY (e.g., run 'openssl rand -hex 32')."
echo ""
echo "3. Set up the backend:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo "   # Open 'psql' and run: CREATE DATABASE <your_db_name>;"
echo "   alembic upgrade head"
echo ""
echo "4. Set up the frontend:"
echo "   cd ../frontend"
echo "   npm install"
echo ""
echo "5. Run the application (in two separate terminals):"
echo "   - Terminal 1 (from backend dir):"
echo "     source venv/bin/activate && uvicorn app.main:app --reload --port 8000"
echo "   - Terminal 2 (from frontend dir):"
echo "     npm run dev"
echo ""
print_info "Refer to 'docs/native_setup_guide.md' for more details."
