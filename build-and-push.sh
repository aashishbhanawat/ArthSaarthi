#!/bin/bash

# This script builds and pushes the Docker images for the backend and frontend services.
# It requires a version tag as an argument.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
# The DOCKER_REGISTRY variable is expected to be set as an environment variable.
# For example: export DOCKER_REGISTRY="your-dockerhub-username"
if [ -z "$DOCKER_REGISTRY" ]; then
  echo "Error: DOCKER_REGISTRY environment variable is not set."
  echo "Please set it to your Docker Hub username or container registry URL."
  exit 1
fi
BACKEND_IMAGE_NAME="pms-backend"
FRONTEND_IMAGE_NAME="pms-frontend"

# --- Versioning ---
# Check if a version tag is provided
if [ -z "$1" ]; then
  echo "Error: No version tag provided."
  echo "Usage: ./build-and-push.sh <version>"
  exit 1
fi
VERSION=$1

# --- Build ---
echo "Building Docker images for version: $VERSION"

echo "Building backend image..."
docker build -t "$DOCKER_REGISTRY/$BACKEND_IMAGE_NAME:$VERSION" -f backend/Dockerfile.prod ./backend
docker tag "$DOCKER_REGISTRY/$BACKEND_IMAGE_NAME:$VERSION" "$DOCKER_REGISTRY/$BACKEND_IMAGE_NAME:latest"

echo "Building frontend image..."
docker build -t "$DOCKER_REGISTRY/$FRONTEND_IMAGE_NAME:$VERSION" -f frontend/Dockerfile.prod ./frontend
docker tag "$DOCKER_REGISTRY/$FRONTEND_IMAGE_NAME:$VERSION" "$DOCKER_REGISTRY/$FRONTEND_IMAGE_NAME:latest"

echo "Docker images built and tagged successfully."

# --- Push ---
echo "Pushing Docker images to the registry..."

echo "Pushing backend image..."
docker push "$DOCKER_REGISTRY/$BACKEND_IMAGE_NAME:$VERSION"
docker push "$DOCKER_REGISTRY/$BACKEND_IMAGE_NAME:latest"

echo "Pushing frontend image..."
docker push "$DOCKER_REGISTRY/$FRONTEND_IMAGE_NAME:$VERSION"
docker push "$DOCKER_REGISTRY/$FRONTEND_IMAGE_NAME:latest"

echo "Docker images pushed to the registry successfully."
echo "Release version $VERSION is complete."
