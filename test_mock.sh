#!/usr/bin/env bash
# Test the state machine with wait-and-touch.sh as a mock agent.
# This simulates the full loop.

set -euo pipefail

echo "=== Setting up test environment ==="
rm -rf signals output backlog.txt vasuki.signal
mkdir -p signals output
chmod +x scripts/*.sh git_commit.sh wait-and-touch.sh

# Create a backlog so the first GATE sees non-empty backlog and continues
echo "iter 1 task" > backlog.txt

echo ""
echo "=== Running state machine (1 iteration) ==="
python3 state_machine.py || true

echo ""
echo "=== Checking output ==="
ls -la output/ 2>/dev/null || echo "(no output dir)"
ls -la signals/ 2>/dev/null || echo "(no signals dir)"
echo ""
echo "=== backlog.txt contents ==="
cat backlog.txt 2>/dev/null || echo "(empty)"
echo ""
echo "=== Test complete ==="
