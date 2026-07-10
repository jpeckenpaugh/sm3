#!/bin/bash
# lint_code.sh — Run static analysis on a Python file
# Usage: lint_code.sh <file_path> [--rules <codes>]

FILE=""
RULES=""

while [ $# -gt 0 ]; do
    case "$1" in
        --rules) RULES="$2"; shift 2 ;;
        *) FILE="$1"; shift ;;
    esac
done

if [ -z "$FILE" ]; then
    echo '{"error": "No file path provided"}'
    exit 1
fi

if [ ! -f "$FILE" ]; then
    echo '{"error": "File not found: '"$FILE"'"}'
    exit 1
fi

# Prefer pyflakes for fast, focused analysis (F-codes)
if command -v pyflakes &> /dev/null; then
    OUTPUT=$(pyflakes "$FILE" 2>&1)
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo '{"file": "'"$FILE"'", "valid": true, "issues": [], "error_count": 0, "warning_count": 0, "style_count": 0}'
    else
        echo '{'
        echo '  "file": "'"$FILE"'",'
        echo '  "valid": false,'
        echo '  "issues": ['
        FIRST=true
        ERRORS=0
        WARNINGS=0
        STYLE=0
        while IFS=: read -r LINE COL MSG; do
            CODE=$(echo "$MSG" | awk '{print $1}')
            MESSAGE=$(echo "$MSG" | sed 's/^[[:space:]]*[A-Z0-9]* //')
            if [ "$FIRST" = true ]; then
                FIRST=false
            else
                echo ','
            fi
            SEVERITY="warning"
            case "$CODE" in
                F821|F822|F823|F831) SEVERITY="error"; ERRORS=$((ERRORS + 1)) ;;
                E*) SEVERITY="style"; STYLE=$((STYLE + 1)) ;;
                *) WARNINGS=$((WARNINGS + 1)) ;;
            esac
            echo "    {\"line\": $LINE, \"column\": ${COL:-0}, \"code\": \"$CODE\", \"message\": \"$(echo "$MESSAGE" | sed 's/"/\\"/g' | xargs)\", \"severity\": \"$SEVERITY\"}"
        done <<< "$OUTPUT"
        echo ''
        echo '  ],'
        echo '  "error_count": '"$ERRORS"','
        echo '  "warning_count": '"$WARNINGS"','
        echo '  "style_count": '"$STYLE"
        echo '}'
    fi
    exit $EXIT_CODE
fi

# Fallback: use python3 -m py_compile
python3 -c "
import ast, sys, py_compile, json
try:
    py_compile.compile('$FILE', doraise=True)
    print(json.dumps({'file': '$FILE', 'valid': True, 'issues': [], 'error_count': 0, 'warning_count': 0, 'style_count': 0}))
except py_compile.PyCompileError as e:
    print(json.dumps({'file': '$FILE', 'valid': False, 'issues': [{'line': 0, 'column': 0, 'code': 'E000', 'message': str(e), 'severity': 'error'}], 'error_count': 1, 'warning_count': 0, 'style_count': 0}))
    sys.exit(1)
" 2>&1
