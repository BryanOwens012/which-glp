#!/bin/bash
# Start the FastAPI ML service

# Get the script's directory and navigate to repo root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

cd "$REPO_ROOT"

# Activate virtual environment
source "$REPO_ROOT/venv/bin/activate"

# Set port from environment or default to 8001
ML_PORT=${ML_PORT:-8001}

echo "Starting WhichGLP ML API on port $ML_PORT..."

# Run the API
cd "$REPO_ROOT/apps/ml"
python3 api.py
