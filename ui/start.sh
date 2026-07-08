#!/bin/bash
# Start the genesis-sm dashboard
# Usage: SM_DB_PATH=/path/to/db.db ./start.sh [port]
PORT=${1:-8001}
cd "$(dirname "$0")"
python3 -m uvicorn main:app --host 0.0.0.0 --port "$PORT"
