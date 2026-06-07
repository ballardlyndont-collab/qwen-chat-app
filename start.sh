#!/bin/bash
set -e

echo "Starting Qwen Chat App..."

trap 'kill $NGINX_PID $UVICORN_PID' SIGTERM SIGINT

# Start nginx in background
nginx -g 'daemon off;' &
NGINX_PID=$!

# Start FastAPI backend in background
cd /app
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

wait $UVICORN_PID
