#!/usr/bin/env bash
# phase_review.sh — REVIEW phase: review produced artifacts.

PHASE="$1"
ITER="$2"

echo "[REVIEW] Iteration $ITER — reviewing artifacts..."
if [ -f "output/iter_${ITER}.txt" ]; then
    echo "[REVIEW] Artifact found: output/iter_${ITER}.txt"
    cat "output/iter_${ITER}.txt"
else
    echo "[REVIEW] No artifact found for iteration $ITER."
fi
echo "[REVIEW] Review complete for iteration $ITER."
exit 0
