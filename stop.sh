#!/bin/bash

echo "Stopping Personal Portfolio Management System..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
echo "Application stopped."