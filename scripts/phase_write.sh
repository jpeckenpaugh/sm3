#!/usr/bin/env bash
# phase_write.sh — WRITE phase: produce output for the iteration.

PHASE="$1"
ITER="$2"
OUTPUT_DIR="output"
mkdir -p "$OUTPUT_DIR"

echo "[WRITE] Iteration $ITER — writing artifacts..."
echo "artifact from iteration $ITER" > "$OUTPUT_DIR/iter_${ITER}.txt"
echo "[WRITE] Write complete for iteration $ITER."
exit 0
