#!/usr/bin/env bash
# verify_syntax.sh — Check all scripts for syntax errors

set -euo pipefail

echo "◆ Checking Python syntax..."
python3 -c "
import py_compile, sys
files = ['state_machine.py']
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f'  ✓ {f}')
    except py_compile.PyCompileError as e:
        print(f'  ✗ {f}: {e}')
        sys.exit(1)
"

echo "◆ Checking shell syntax..."
for f in git_commit.sh wait-and-touch.sh run_matsya.sh scripts/*.sh verify_syntax.sh; do
    if [ -f "$f" ]; then
        if bash -n "$f" 2>/dev/null; then
            echo "  ✓ $f"
        else
            echo "  ✗ $f: syntax error"
            bash -n "$f"
        fi
    fi
done

echo ""
echo "◆ All syntax checks passed."
