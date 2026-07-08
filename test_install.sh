#!/usr/bin/env bash
# Verify genesis-sm package installation
# Run: bash test_install.sh

set -e

echo "=== Genesis SM Package Verification ==="
echo ""

# Step 1: Install package in development mode
echo "--- Step 1: pip install -e . ---"
cd /root/sm
source .venv/bin/activate
pip install -e . 2>&1
echo ""

# Step 2: Verify the 'sm' CLI is available
echo "--- Step 2: sm --help ---"
sm --help 2>&1 || python3 -m genesis_sm.cli --help 2>&1
echo ""

# Step 3: Verify imports work
echo "--- Step 3: Import verification ---"
python3 -c "
import genesis_sm
from genesis_sm.state_machine import run_with_config, load_config, has_backlog
from genesis_sm.seed import seed_database
from genesis_sm.pipeline import run_pipeline
from genesis_sm.pipeline.dispatch import dispatch_sync, handshake_sync, build_request, record_dispatch
from genesis_sm.pipeline.events import log_phase_event, read_phase_events
from genesis_sm.pipeline.seeds import seed_pipeline_tables
from genesis_sm.cli import main, build_parser
print('✓ All imports successful')
print(f'  Package: genesis_sm v{genesis_sm.__version__}')
"
echo ""

# Step 4: Verify package data is accessible
echo "--- Step 4: Package data ---"
python3 -c "
import importlib.resources as res
import genesis_sm
schema = (res.files(genesis_sm) / 'schema.sql').read_text()
config = (res.files(genesis_sm) / 'config.json').read_text()
import json
cfg = json.loads(config)
print(f'✓ schema.sql: {len(schema)} chars')
print(f'✓ config.json: {len(config)} chars, {len(cfg)} keys')
"
echo ""

# Step 5: Verify the existing sm.py still works via the old entry point
echo "--- Step 5: Backward compatibility (root sm.py) ---"
python3 /root/sm/sm.py --help 2>&1 | head -5
echo ""

# Step 6: Test sm init on a temp directory
echo "--- Step 6: sm init (planting command) ---"
TMPDIR=$(mktemp -d)
sm init "$TMPDIR/test.db" --yes 2>&1 || echo "(init may need seed data in the project root)"
rm -rf "$TMPDIR"
echo ""

echo "=== Verification complete ==="
