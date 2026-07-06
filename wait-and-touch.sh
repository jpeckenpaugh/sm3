#!/usr/bin/env bash
# wait-and-touch.sh — Mock agent for Matsya state machine verification.
# Waits for a trigger file, then touches a completion signal.
#
# Usage: wait-and-touch.sh <watch_file> <touch_file>
#   watch_file  — file to poll for existence
#   touch_file  — file to create when watch_file appears
#
# Phase agent protocol (called by state_machine.py):
#   wait-and-touch.sh <phase_name> <iteration>
#   Watches for backlog.txt, then touches a per-iteration signal.

WATCH_FILE="${1:-backlog.txt}"
TOUCH_FILE="${2:-signal.touch}"
POLL_SECS="${POLL_SECS:-1}"

if [ "$#" -ge 1 ] && [ "$1" != "${1#/}" ]; then
    # Called by state machine: args are phase name and iteration
    PHASE="$1"
    ITER="$2"
    WATCH_FILE="backlog.txt"
    TOUCH_FILE="signals/${PHASE}_${ITER}.done"
    mkdir -p signals
fi

echo "wait-and-touch.sh: watching for '$WATCH_FILE' → touch '$TOUCH_FILE'"

while true; do
    if [ -f "$WATCH_FILE" ]; then
        touch "$TOUCH_FILE"
        echo "  ✓ Detected '$WATCH_FILE', touched '$TOUCH_FILE'"
        exit 0
    fi
    sleep "$POLL_SECS"
done
