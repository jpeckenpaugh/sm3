#!/usr/bin/env bash
# phase_gate.sh — GATE phase: check backlog and signal.

PHASE="$1"
ITER="$2"
BACKLOG_FILE="${BACKLOG_FILE:-backlog.txt}"
SIGNAL_FILE="${SIGNAL_FILE:-vasuki.signal}"

echo "[GATE] Iteration $ITER — checking backlog..."

if [ -f "$BACKLOG_FILE" ] && [ -s "$BACKLOG_FILE" ]; then
    echo "[GATE] Backlog non-empty. Continuing iteration."
    exit 0
else
    echo "[GATE] Backlog empty. Waiting for Vasuki signal..."
    while [ ! -f "$SIGNAL_FILE" ]; do
        sleep 2
    done
    echo "[GATE] Signal received from Vasuki."
    exit 0
fi
