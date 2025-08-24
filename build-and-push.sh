#!/bin/bash

# This script builds the Docker images for the backend and frontend services.
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

# --- Build Configuration ---
PUSH_FLAG="--load" # Default to --load for local safety, which loads the image to the local docker daemon
PLATFORM_FLAG=""   # Default to native platform for local builds

# If --push is passed, build for multi-arch and set the push flag
if [ "$2" = "--push" ]; then
    PUSH_FLAG="--push"
    PLATFORM_FLAG="--platform linux/amd64,linux/arm64"
    echo "Running in --push mode. Images will be pushed to the registry."
else
    echo "Running in local mode. Images will be built for the native architecture and loaded into the local Docker daemon."
fi

# --- Build ---
echo "Building Docker images for version: $VERSION"

BUILDER_NAME="arthsaarthi-builder"
echo "Setting up docker buildx builder '$BUILDER_NAME'..."
if ! docker buildx inspect "$BUILDER_NAME" >/dev/null 2>&1; then
    echo "Builder '$BUILDER_NAME' not found. Creating it..."
    docker buildx create --use --name "$BUILDER_NAME"
else
    echo "Builder '$BUILDER_NAME' already exists. Using it."
    docker buildx use "$BUILDER_NAME"
fi

echo "Building multi-architecture backend image..."
docker buildx build \
  $PLATFORM_FLAG \
  -t "$DOCKER_REGISTRY/$BACKEND_IMAGE_NAME:$VERSION" \
  -t "$DOCKER_REGISTRY/$BACKEND_IMAGE_NAME:latest" \
  -f backend/Dockerfile.prod ./backend $PUSH_FLAG

echo "Building multi-architecture frontend image..."
docker buildx build \
  $PLATFORM_FLAG \
  -t "$DOCKER_REGISTRY/$FRONTEND_IMAGE_NAME:$VERSION" \
  -t "$DOCKER_REGISTRY/$FRONTEND_IMAGE_NAME:latest" \
  -f frontend/Dockerfile.prod ./frontend $PUSH_FLAG

echo "Docker images built successfully."
if [ "$PUSH_FLAG" = "--push" ]; then
    echo "Images have been pushed to the registry."
fi

echo "Release version $VERSION is complete."
