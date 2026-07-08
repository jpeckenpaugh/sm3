#!/bin/bash
# file_tree.sh — Show directory tree structure
# Usage: file_tree.sh [--root <path>] [--depth <n>] [--dirs-only] [--pattern <glob>]

ROOT="."
DEPTH=3
DIRS_ONLY="false"
PATTERN=""

while [ $# -gt 0 ]; do
    case "$1" in
        --root) ROOT="$2"; shift 2 ;;
        --depth) DEPTH="$2"; shift 2 ;;
        --dirs-only) DIRS_ONLY="true"; shift ;;
        --pattern) PATTERN="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [ ! -d "$ROOT" ]; then
    echo '{"error": "Directory not found: '"$ROOT"'"}'
    exit 1
fi

cd "$ROOT" || exit 1

if command -v tree &> /dev/null; then
    TREE_OPTS="-L $DEPTH --charset=utf-8"
    if [ "$DIRS_ONLY" = "true" ]; then
        TREE_OPTS="$TREE_OPTS -d"
    fi
    if [ -n "$PATTERN" ]; then
        TREE_OPTS="$TREE_OPTS -P '$PATTERN'"
    fi
    eval tree $TREE_OPTS 2>/dev/null
else
    # Fallback to find
    FIND_OPTS="."
    if [ "$DIRS_ONLY" = "true" ]; then
        find . -maxdepth "$DEPTH" -type d 2>/dev/null | sort
    else
        find . -maxdepth "$DEPTH" -type f -o -type d 2>/dev/null | sort
    fi
fi
