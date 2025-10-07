#!/bin/bash
set -e
echo "Starting WhichGLP Post Ingestion Service..."
if [ -d "../../venv" ]; then
    source ../../venv/bin/activate
fi
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../..:$(pwd)/.."
PORT=${PORT:-8003}
cd "$(dirname "$0")"
python3 -m uvicorn api:app --host 0.0.0.0 --port $PORT --log-level info
