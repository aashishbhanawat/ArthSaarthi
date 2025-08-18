#!/bin/bash
set -ex

echo "--- Cleaning up old builds ---"
rm -rf backend/build backend/dist frontend/dist-electron frontend/electron

echo "--- Copying electron files ---"
cp -r electron frontend/

echo "--- Building Backend ---"
(cd backend && pyinstaller build-backend.spec)

echo "--- Building Frontend and Packaging ---"
(cd frontend && npm install && npm run build && npm run dist)

echo "--- Build Complete ---"
find frontend/dist-electron -name "*.AppImage"
