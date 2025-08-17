#!/bin/bash
set -e

echo "Building backend..."
(cd backend && pyinstaller --noconfirm --clean build-backend.spec)

echo "Building frontend..."
(cd frontend && npm install && npm run build)

echo "Copying backend to frontend..."
mkdir -p frontend/dist-backend
cp -r backend/dist/backend_dist/* frontend/dist-backend/

echo "Packaging application..."
(cd frontend && npm run electron:build)

echo "Build complete. Find the artifacts in frontend/release."
