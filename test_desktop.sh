#!/bin/bash
set -e

docker compose -f docker-compose.yml -f docker-compose.test.desktop.yml up --build --abort-on-container-exit
