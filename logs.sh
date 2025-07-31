#!/bin/bash

echo "Showing logs for all services. Press Ctrl+C to exit."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f