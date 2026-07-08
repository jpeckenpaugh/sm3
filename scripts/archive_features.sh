#!/usr/bin/env bash
# archive_features.sh — Archive completed feature files
#
# Moves feature files from backlog/ to backlog/archive/{sprint_num}/
# for features that were included in the given sprint.
#
# Usage:
#   bash scripts/archive_features.sh <sprint_num>
#
# Example:
#   bash scripts/archive_features.sh 001
#
# Reads sprint/{sprint_num}/features/ft-*.md and for each file found
# there, checks if it exists in backlog/. If it does, moves it to
# backlog/archive/{sprint_num}/.

set -e

if [ -z "$1" ]; then
    echo "Usage: bash scripts/archive_features.sh <sprint_num>"
    exit 1
fi

SPRINT_NUM="$1"
SPRINT_FEATURES_DIR="sprint/${SPRINT_NUM}/features"
BACKLOG_DIR="backlog"
ARCHIVE_DIR="backlog/archive/${SPRINT_NUM}"

if [ ! -d "$SPRINT_FEATURES_DIR" ]; then
    echo "No features directory found at ${SPRINT_FEATURES_DIR} — nothing to archive."
    exit 0
fi

mkdir -p "$ARCHIVE_DIR"

ARCHIVED=0
NOT_FOUND=0

for feature_file in "$SPRINT_FEATURES_DIR"/ft-*.md; do
    if [ ! -f "$feature_file" ]; then
        continue
    fi

    basename=$(basename "$feature_file")

    if [ -f "${BACKLOG_DIR}/${basename}" ]; then
        mv "${BACKLOG_DIR}/${basename}" "${ARCHIVE_DIR}/${basename}"
        echo "  ✓ Archived: ${basename}"
        ARCHIVED=$((ARCHIVED + 1))
    else
        echo "  ⚠  Not in backlog: ${basename}"
        NOT_FOUND=$((NOT_FOUND + 1))
    fi
done

echo ""
echo "  Archive complete: ${ARCHIVED} feature(s) archived, ${NOT_FOUND} not found in backlog."
