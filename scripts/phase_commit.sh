#!/usr/bin/env bash
# phase_commit.sh — COMMIT phase.
# Simulates a commit by creating a marker file.

PHASE="$1"
ITER="$2"

mkdir -p output
echo "commit-marker-iter-${ITER}" > "output/commit_${ITER}.marker"
echo "[COMMIT] Iteration $ITER — commit marker created."
exit 0
