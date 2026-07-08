#!/bin/bash
# list_files.sh — List files matching a glob pattern
# Usage: list_files.sh <pattern> [--root <path>] [--max <n>]

PATTERN=""
ROOT="."
MAX=200

while [ $# -gt 0 ]; do
    case "$1" in
        --root) ROOT="$2"; shift 2 ;;
        --max) MAX="$2"; shift 2 ;;
        *) PATTERN="$1"; shift ;;
    esac
done

if [ -z "$PATTERN" ]; then
    echo '{"error": "No pattern provided"}'
    exit 1
fi

if [ ! -d "$ROOT" ]; then
    echo '{"error": "Directory not found: '"$ROOT"'"}'
    exit 1
fi

cd "$ROOT" || exit 1
RESULTS=$(find . -path "./$PATTERN" -type f 2>/dev/null | head -n "$MAX")
COUNT=$(echo "$RESULTS" | grep -c .)
TRUNCATED="false"

if [ "$COUNT" -ge "$MAX" ]; then
    TRUNCATED="true"
fi

echo '{'
echo '  "files": ['
FIRST=true
while IFS= read -r FILE; do
    if [ -n "$FILE" ]; then
        if [ "$FIRST" = true ]; then
            FIRST=false
        else
            echo ','
        fi
        echo "    \"$FILE\""
    fi
done <<< "$RESULTS"
echo ''
echo '  ],'
echo '  "count": '"$COUNT"','
echo '  "truncated": '"$TRUNCATED"
echo '}'
