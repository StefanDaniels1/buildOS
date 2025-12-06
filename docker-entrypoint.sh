#!/bin/bash
# Docker entrypoint script for buildOS backend
# Fixes volume permissions then runs as non-root user
#
# This script runs as root on container start, fixes ownership of
# mounted volumes (which may be owned by root from previous deployments),
# then switches to the buildos user to run the server.

set -e

# Fix ownership of mounted volumes
# These directories are mounted as Docker volumes and may have been
# created by a previous container running as root
echo "Fixing volume permissions..."
chown -R buildos:buildos /app/uploads /app/workspace /app/.logs 2>/dev/null || true

# Switch to buildos user and run the server
echo "Starting server as buildos user..."
exec gosu buildos bun run src/index.ts
