#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Load environment variables if .env exists
if [ -f ".env" ]; then
  set -a
  source ".env"
  set +a
fi

BACKEND_PORT="${BACKEND_PORT:-3001}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
export RAG_EMBED_PROVIDER="${RAG_EMBED_PROVIDER:-local}"
export RAG_EXCLUDE_PATHS="${RAG_EXCLUDE_PATHS:-1. 지방의회 회의록}"
export RAG_SKIP_PDF="${RAG_SKIP_PDF:-true}"

echo "Starting backend on port ${BACKEND_PORT} (RAG provider: ${RAG_EMBED_PROVIDER})"
PORT="${BACKEND_PORT}" pnpm --filter @napo/backend exec ts-node --require tsconfig-paths/register --prefer-ts-exts --transpile-only src/index.ts &
BACK_PID=$!

echo "Starting frontend on port ${FRONTEND_PORT}"
PORT="${FRONTEND_PORT}" pnpm --filter @napo/frontend exec vite --host 0.0.0.0 --port "${FRONTEND_PORT}" --strictPort &
FRONT_PID=$!

cleanup() {
  echo "Stopping dev servers..."
  kill "$BACK_PID" "$FRONT_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

wait
