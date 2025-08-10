#!/bin/bash

# This script helps configure the application for the first time.

ENV_FILE="backend/.env.prod"
ENV_EXAMPLE_FILE="backend/.env.prod.example"

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

if [ -f "$ENV_FILE" ]; then
  echo_yellow "Configuration file '$ENV_FILE' already exists."
  echo "If you need to reconfigure, please delete it and run this script again."
  exit 0
fi

echo "Creating production configuration file from example..."
cp "$ENV_EXAMPLE_FILE" "$ENV_FILE"

echo "Generating a new secure SECRET_KEY..."
SECRET_KEY=$(openssl rand -hex 32)

# Use sed to replace the placeholder SECRET_KEY= with the new key.
sed -i.bak "s|SECRET_KEY=|SECRET_KEY=$SECRET_KEY|" "$ENV_FILE" && rm "${ENV_FILE}.bak"

echo "Setting default ALLOWED_HOSTS in $ENV_FILE..."
echo -e "\n# A comma-separated list of domains to allow for Vite's dev server\nALLOWED_HOSTS=localhost" >> "$ENV_FILE"

echo_green "Configuration file '$ENV_FILE' created successfully."
echo_yellow "IMPORTANT: You must now edit this file to set your CORS_ORIGINS."
echo "Set CORS_ORIGINS to the domain name or IP address you will use to access the app."
echo "Example: CORS_ORIGINS=http://192.168.1.50,https://pms.your-domain.com"
echo ""
echo "After editing, you can start the application by running ./start.sh"