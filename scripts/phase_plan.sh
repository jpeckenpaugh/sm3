#!/usr/bin/env bash
# phase_plan.sh — PLAN phase: simulate planning by waiting for backlog.

PHASE="$1"
ITER="$2"
SIGNAL_DIR="signals"
mkdir -p "$SIGNAL_DIR"

echo "[PLAN] Iteration $ITER — waiting for backlog..."
# Simulate: just succeed
echo "[PLAN] Planning complete for iteration $ITER."
exit 0
