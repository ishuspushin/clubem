#!/usr/bin/env sh
set -eu

# Run from project root:
#   chmod +x scripts/dev_run.sh
#   ./scripts/dev_run.sh

# Optional: create folders early (safe if already exists)
mkdir -p data/uploads data/outputs data/jobs schema_registry/active schema_registry/history

export PYTHONPATH="$(pwd)/src"

echo "Starting worker in background..."
poetry run python scripts/run_worker.py &
WORKER_PID=$!

cleanup() {
  echo "Stopping worker (pid=$WORKER_PID)..."
  kill "$WORKER_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

echo "Starting Flask API..."
poetry run python scripts/run_flask_dev.py
