#!/bin/bash

echo "Starting Personal Portfolio Management System in Production Mode..."

# Check if the .env.prod file exists. If not, guide the user.
if [ ! -f "backend/.env.prod" ]; then
    echo -e "\033[0;31mError: Production environment file 'backend/.env.prod' not found.\033[0m"
    echo "Please run './configure.sh' first to set up your environment."
    exit 1
fi

docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo -e "\n\033[0;32mApplication started successfully!\033[0m"
echo "You can access it at http://localhost (or your configured domain/IP)."
echo "To view logs, run: ./logs.sh"
echo "To stop the application, run: ./stop.sh"