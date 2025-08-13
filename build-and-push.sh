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
BACKEND_IMAGE_NAME="arthsaarthi-backend"
FRONTEND_IMAGE_NAME="arthsaarthi-frontend"

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

echo "Setting up docker buildx..."
docker buildx create --use --name pms-builder

echo "Building and pushing multi-architecture backend image..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t "$DOCKER_REGISTRY/$BACKEND_IMAGE_NAME:$VERSION" \
  -t "$DOCKER_REGISTRY/$BACKEND_IMAGE_NAME:latest" \
  -f backend/Dockerfile.prod ./backend --push

echo "Building and pushing multi-architecture frontend image..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t "$DOCKER_REGISTRY/$FRONTEND_IMAGE_NAME:$VERSION" \
  -t "$DOCKER_REGISTRY/$FRONTEND_IMAGE_NAME:latest" \
  -f frontend/Dockerfile.prod ./frontend --push

echo "Docker images built and pushed to the registry successfully."

echo "Release version $VERSION is complete."
