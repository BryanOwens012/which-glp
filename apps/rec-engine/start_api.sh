#!/bin/bash
# Start the FastAPI rec-engine service

# Get the script's directory and navigate to repo root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

cd "$REPO_ROOT"

# Activate virtual environment
source "$REPO_ROOT/venv/bin/activate"

# Set port from environment or default to 8001
REC_ENGINE_PORT=${REC_ENGINE_PORT:-8001}

echo "Starting WhichGLP Rec Engine API on port $REC_ENGINE_PORT..."

# Run the API
cd "$REPO_ROOT/apps/rec-engine"
python3 api.py
