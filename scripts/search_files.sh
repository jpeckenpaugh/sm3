#!/bin/bash
# search_files.sh — Grep across the project
# Usage: search_files.sh <pattern> [--path <path>] [--include <glob>] [--regex] [--max <n>]

PATTERN=""
ROOT="."
INCLUDE=""
REGEX="false"
MAX=50

while [ $# -gt 0 ]; do
    case "$1" in
        --path) ROOT="$2"; shift 2 ;;
        --include) INCLUDE="$2"; shift 2 ;;
        --regex) REGEX="true"; shift ;;
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

if [ "$REGEX" = "true" ]; then
    GREP_OPTS="-r -n"
else
    GREP_OPTS="-r -n -F"
fi

if [ -n "$INCLUDE" ]; then
    GREP_OPTS="$GREP_OPTS --include=$INCLUDE"
fi

RESULTS=$(eval grep $GREP_OPTS "$PATTERN" "$ROOT" 2>/dev/null)
TOTAL=$(echo "$RESULTS" | grep -c .)
if [ "$TOTAL" -gt "$MAX" ]; then
    RESULTS=$(echo "$RESULTS" | head -n "$MAX")
    TRUNCATED="true"
else
    TRUNCATED="false"
fi
COUNT=$(echo "$RESULTS" | grep -c . || true)

echo '{'
echo '  "matches": '"$COUNT"','
echo '  "results": ['
if [ "$COUNT" -gt 0 ]; then
    FIRST=true
    while IFS=: read -r FILE LINE CONTENT; do
        if [ -n "$FILE" ]; then
            if [ "$FIRST" = true ]; then
                FIRST=false
            else
                echo ','
            fi
            CONTENT_ESCAPED=$(echo "$CONTENT" | sed 's/"/\\"/g')
            echo "    {\"file\":\"$FILE\",\"line\":$LINE,\"content\":\"$CONTENT_ESCAPED\"}"
        fi
    done <<< "$RESULTS"
fi
echo ''
echo '  ],'
echo '  "truncated": '"$TRUNCATED"
echo '}'
