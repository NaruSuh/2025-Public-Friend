#!/bin/bash
set -e

echo "=== naPO HuggingFace Spaces ==="
echo "Starting backend (port 3001)..."

# Start Node.js backend in background
cd /app/apps/backend
node dist/index.js &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend..."
for i in $(seq 1 30); do
    if wget -qO- http://127.0.0.1:3001/health > /dev/null 2>&1; then
        echo "Backend ready!"
        break
    fi
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "ERROR: Backend process died"
        exit 1
    fi
    sleep 1
done

echo "Starting nginx (port 7860)..."

# Cleanup on exit
cleanup() {
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $NGINX_PID 2>/dev/null || true
    exit 0
}
trap cleanup TERM INT

# Start nginx in foreground
nginx -g "daemon off;" &
NGINX_PID=$!

echo "=== naPO is running on port 7860 ==="

# Wait for either process to exit
wait -n $BACKEND_PID $NGINX_PID 2>/dev/null || wait $BACKEND_PID
echo "Process exited unexpectedly"
cleanup
