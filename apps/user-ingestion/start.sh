#!/bin/bash
# Startup script for user-ingestion service on Railway

set -e

echo "Starting WhichGLP User Ingestion Service..."

# Activate virtual environment (if running locally)
if [ -d "../../venv" ]; then
    echo "Activating virtual environment..."
    source ../../venv/bin/activate
fi

# Install dependencies (Railway will do this automatically via requirements.txt)
# pip install -r ../../requirements.txt

# Set Python path to include parent directories
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../..:$(pwd)/.."

# Railway sets PORT automatically, default to 8002 for local dev
PORT=${PORT:-8002}

echo "Starting FastAPI service on port $PORT..."

# Start the FastAPI server
cd "$(dirname "$0")"
python3 -m uvicorn api:app --host 0.0.0.0 --port $PORT --log-level info
