#!/bin/bash
# Install dependencies for the genesis-sm Operator Dashboard
# Run: bash install.sh

set -e

echo "=== genesis-sm Dashboard Install ==="
echo ""

# ── Install Python dependencies ──────────────────────────────────────────────
echo "--- Installing Python packages ---"
python3 -m pip install fastapi uvicorn jinja2 2>&1 | tail -5
echo ""

# ── Verify imports ───────────────────────────────────────────────────────────
echo "--- Verifying imports ---"
python3 -c "
import fastapi; print(f'  ✓ fastapi {fastapi.__version__}')
import uvicorn; print(f'  ✓ uvicorn')
import jinja2;  print(f'  ✓ jinja2 {jinja2.__version__}')
"
echo ""

# ── Check for config ────────────────────────────────────────────────────────
if [ ! -f "$HOME/.sm-dash.json" ]; then
    echo "  ⚠ No ~/.sm-dash.json found — multi-DB mode disabled"
    echo "    Create one with:"
    echo '    echo '"'"'{"databases": [{"name": "My Container", "path": "/path/to/matsya.db"}]}'"'"' > ~/.sm-dash.json'
    echo ""
fi

echo "=== Install complete ==="
echo ""
echo "Start the dashboard:"
echo "  bash start.sh [port]"
echo ""
echo "Or with a specific database:"
echo "  SM_DB_PATH=/path/to/matsya.db bash start.sh"
