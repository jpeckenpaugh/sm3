#!/usr/bin/env bash
# archive-signals.sh — Archive sprint signals into dated directory
#
# Moves all .md files from signals/ into signals/archive/YYYY-MM-DD/
# preserving the conversation history between Trimurti aspects.
#
# Usage:
#   bash scripts/archive-signals.sh              # archive to today's date
#   bash scripts/archive-signals.sh --date 2026-07-08  # specific date
#
# See trimurti/signal-archive-protocol.md for the full specification.

set -e
cd "$(dirname "$0")/.."

# Determine archive date
if [ "$1" == "--date" ] && [ -n "$2" ]; then
    ARCHIVE_DATE="$2"
else
    ARCHIVE_DATE="$(date +%Y-%m-%d)"
fi

SIGNALS_DIR="signals"
ARCHIVE_DIR="${SIGNALS_DIR}/archive/${ARCHIVE_DATE}"

# Check if there are any signals to archive
shopt -s nullglob
signal_files=("${SIGNALS_DIR}"/*.md)
shopt -u nullglob

if [ ${#signal_files[@]} -eq 0 ]; then
    echo "  No signals to archive in ${SIGNALS_DIR}/"
    exit 0
fi

# Create archive directory
mkdir -p "${ARCHIVE_DIR}"

# Move each signal file to the archive
COUNT=0
for f in "${signal_files[@]}"; do
    basename=$(basename "$f")
    mv "$f" "${ARCHIVE_DIR}/${basename}"
    echo "  ✓ Archived: ${basename}"
    COUNT=$((COUNT + 1))
done

echo ""
echo "  Archive complete: ${COUNT} signal(s) archived to ${ARCHIVE_DIR}/"
