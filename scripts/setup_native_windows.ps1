# Native Setup Script for Windows
# This script automates the setup of the Personal Portfolio Management System on Windows using PowerShell and Chocolatey.

# --- Helper Functions ---
function Print-Info {
    param ([string]$message)
    Write-Host "[INFO] $message" -ForegroundColor Cyan
}

function Print-Success {
    param ([string]$message)
    Write-Host "[SUCCESS] $message" -ForegroundColor Green
}

function Print-Error {
    param ([string]$message)
    Write-Host "[ERROR] $message" -ForegroundColor Red
}

# --- Check for Administrator Privileges ---
Print-Info "Checking for Administrator privileges..."
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Print-Error "This script must be run as Administrator to install software with Chocolatey."
    Print-Info "Please re-run this script in a PowerShell window with Administrator rights."
    exit 1
}

# --- Check for Chocolatey ---
Print-Info "Checking for Chocolatey package manager..."
if (-NOT (Get-Command choco -ErrorAction SilentlyContinue)) {
    Print-Error "Chocolatey not found. Please install it from https://chocolatey.org/install"
    Print-Info "After installing Chocolatey, please re-run this script."
    exit 1
}

# --- Main Setup ---
Print-Info "Starting native setup for Windows..."

# Install Dependencies
Print-Info "Installing dependencies: Python, Node.js, PostgreSQL, Redis..."
# Note: Specific versions are used to match the project's tested environment.
choco install python --version=3.11.5 -y
choco install nodejs --version=18.17.1 -y
choco install postgresql13 -y
choco install redis-64 -y

Print-Success "All dependencies installed."
Print-Info "PostgreSQL and Redis should be running as services. You may need to configure your PostgreSQL user and password manually."

# --- Manual Steps ---
Write-Host ""
Print-Info "Next steps are manual:"
Write-Host "1. Clone the project repository if you haven't already."
Write-Host "   git clone <repository-url>"
Write-Host "   cd personal-portfolio-management-system"
Write-Host ""
Write-Host "2. Configure the backend environment:"
Write-Host "   cd backend"
Write-Host "   copy .env.prod.example .env"
Write-Host "   - Edit the '.env' file in a text editor:"
Write-Host "   - Set POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB."
Write-Host "   - Generate and set a SECRET_KEY."
Write-Host ""
Write-Host "3. Set up the backend:"
Write-Host "   python -m venv venv"
Write-Host "   .\venv\Scripts\activate"
Write-Host "   pip install -r requirements.txt"
Write-Host "   # Open 'psql' and run: CREATE DATABASE <your_db_name>;"
Write-Host "   alembic upgrade head"
Write-Host ""
Write-Host "4. Set up the frontend:"
Write-Host "   cd ..\frontend"
Write-Host "   npm install"
Write-Host ""
Write-Host "5. Run the application (in two separate terminals):"
Write-Host "   - Terminal 1 (from backend dir):"
Write-Host "     .\venv\Scripts\activate; uvicorn app.main:app --reload --port 8000"
Write-Host "   - Terminal 2 (from frontend dir):"
Write-Host "     npm run dev"
Write-Host ""
Print-Info "Refer to 'docs/native_setup_guide.md' for more details."
