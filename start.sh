#!/bin/bash
set -e

echo "Starting Qwen Chat App..."

# Start nginx in background
nginx -g 'daemon off;' &
NGINX_PID=$!

# Start FastAPI backend
cd /app
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Handle SIGTERM
trap "kill $NGINX_PID" SIGTERM

wait
