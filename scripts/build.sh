#!/bin/bash
set -euo pipefail

NO_CACHE=${1:-""}

echo "Building all images..."
if [ "$NO_CACHE" = "--no-cache" ]; then
    DOCKER_BUILDKIT=1 docker compose build --no-cache
else
    DOCKER_BUILDKIT=1 docker compose build
fi

echo "All images built successfully."
