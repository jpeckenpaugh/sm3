#!/usr/bin/env bash
# git_commit.sh — Stage all changes and commit with a message.
# Usage: git_commit.sh [message_file]
#   If no argument, reads from stdin.
#   Exits 0 on success, non-zero on failure.

set -euo pipefail

# 1. Stage everything
git add -A

# 2. Get the commit message
if [ $# -ge 1 ] && [ -n "$1" ]; then
    MESSAGE_FILE="$1"
    if [ ! -f "$MESSAGE_FILE" ]; then
        echo "Error: message file not found: $MESSAGE_FILE" >&2
        exit 1
    fi
    COMMIT_MSG=$(cat "$MESSAGE_FILE")
elif [ ! -t 0 ]; then
    # Read from stdin (piped)
    COMMIT_MSG=$(cat)
else
    echo "Error: no commit message provided (pipe one in or pass a file)" >&2
    exit 1
fi

if [ -z "$COMMIT_MSG" ]; then
    echo "Error: commit message is empty" >&2
    exit 1
fi

# 3. Commit
git commit -m "$COMMIT_MSG"
