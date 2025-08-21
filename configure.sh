#!/bin/bash

# This script helps configure the application for the first time.

BACKEND_ENV_FILE="backend/.env.prod"
BACKEND_ENV_EXAMPLE_FILE="backend/.env.prod.example"
FRONTEND_ENV_FILE="frontend/.env"

# --- Helper Functions ---
echo_green() {
  echo -e "\033[0;32m$1\033[0m"
}

echo_yellow() {
  echo -e "\033[1;33m$1\033[0m"
}

echo_red() {
  echo -e "\033[0;31m$1\033[0m"
}

# --- Main Logic ---
echo_green "--- PMS Pilot Release Configuration ---"

if [ -f "$BACKEND_ENV_FILE" ]; then
  echo_yellow "Configuration file '$BACKEND_ENV_FILE' already exists."
  echo "If you need to reconfigure, please delete it and run this script again."
  exit 0
fi

echo "Creating production configuration file from example..."
cp "$BACKEND_ENV_EXAMPLE_FILE" "$BACKEND_ENV_FILE"

echo "Generating a new secure SECRET_KEY..."
SECRET_KEY=$(openssl rand -hex 32)

# Use sed to replace the placeholder SECRET_KEY= with the new key.
sed -i.bak "s|SECRET_KEY=|SECRET_KEY=$SECRET_KEY|" "$BACKEND_ENV_FILE" && rm "${BACKEND_ENV_FILE}.bak"

echo "Creating frontend environment file '$FRONTEND_ENV_FILE' for development server..."
echo "# A comma-separated list of domains to allow for Vite's dev server" > "$FRONTEND_ENV_FILE"
echo "# Example: ALLOWED_HOSTS=mydomain.com,192.168.1.100" >> "$FRONTEND_ENV_FILE"
echo "ALLOWED_HOSTS=localhost" >> "$FRONTEND_ENV_FILE"

echo_green "Configuration files created successfully."
echo_yellow "IMPORTANT: You must now edit this file to set your CORS_ORIGINS."
echo "File to edit: $BACKEND_ENV_FILE"
echo "Set CORS_ORIGINS to the domain name or IP address you will use to access the app in production."
echo "Example: CORS_ORIGINS=http://192.168.1.50,https://pms.your-domain.com"
echo ""
echo "After editing, you can start the application by running ./start.sh"