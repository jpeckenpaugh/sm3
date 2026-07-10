#!/bin/bash
# compare_files.sh — Compare two files and return structural differences
# Usage: compare_files.sh <file_a> <file_b> [--context <n>] [--mode unified|summary|word]

FILE_A=""
FILE_B=""
CONTEXT=3
MODE="unified"

while [ $# -gt 0 ]; do
    case "$1" in
        --context) CONTEXT="$2"; shift 2 ;;
        --mode) MODE="$2"; shift 2 ;;
        *) 
            if [ -z "$FILE_A" ]; then
                FILE_A="$1"
            elif [ -z "$FILE_B" ]; then
                FILE_B="$1"
            fi
            shift ;;
    esac
done

if [ -z "$FILE_A" ] || [ -z "$FILE_B" ]; then
    echo '{"error": "Two file paths required"}'
    exit 1
fi

if [ ! -f "$FILE_A" ]; then
    echo '{"error": "File not found: '"$FILE_A"'"}'
    exit 1
fi
if [ ! -f "$FILE_B" ]; then
    echo '{"error": "File not found: '"$FILE_B"'"}'
    exit 1
fi

if [ "$MODE" = "summary" ]; then
    if diff -q "$FILE_A" "$FILE_B" > /dev/null 2>&1; then
        echo '{"identical": true, "hunks": 0, "additions": 0, "deletions": 0, "summary": "Files are identical"}'
    else
        DIFF_OUT=$(diff -u "$FILE_A" "$FILE_B" 2>/dev/null)
        HUNKS=$(echo "$DIFF_OUT" | grep -c '^@@' || true)
        [ -z "$HUNKS" ] && HUNKS=0
        ADD=$(echo "$DIFF_OUT" | grep -c '^+' || echo "0")
        DEL=$(echo "$DIFF_OUT" | grep -c '^-' || echo "0")
        # Remove header diff lines from counts
        ADD=$((ADD - 1))
        DEL=$((DEL - 1))
        [ "$ADD" -lt 0 ] && ADD=0
        [ "$DEL" -lt 0 ] && DEL=0
        SUMMARY="$HUNKS hunk(s), $ADD addition(s), $DEL deletion(s)"
        cat <<JSON
{"identical": false, "hunks": $HUNKS, "additions": $ADD, "deletions": $DEL, "summary": "$SUMMARY"}
JSON
    fi
elif [ "$MODE" = "word" ]; then
    diff -u -U "$CONTEXT" "$FILE_A" "$FILE_B" | colordiff 2>/dev/null || diff -u -U "$CONTEXT" "$FILE_A" "$FILE_B"
else
    diff -u -U "$CONTEXT" "$FILE_A" "$FILE_B"
fi
