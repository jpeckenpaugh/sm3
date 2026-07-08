#!/usr/bin/env bash
# Quick syntax check on Python files
python3 -c "import py_compile; py_compile.compile('schema.sql', doraise=False)" 2>&1 || true
python3 -m py_compile sm.py 2>&1
python3 -m py_compile pipeline/events.py 2>&1
python3 -m py_compile pipeline/__init__.py 2>&1
echo "Syntax check complete"
