#!/usr/bin/env bash
# run_matsya.sh — Execute the Matsya state machine with mock agents

set -euo pipefail

echo "╔════════════════════════════════════════════════════╗"
echo "║  Matsya State Machine — Live Run                  ║"
echo "╚════════════════════════════════════════════════════╝"

# Setup
chmod +x scripts/*.sh git_commit.sh wait-and-touch.sh 2>/dev/null || true
mkdir -p signals output

# Initialize schema
echo ""
echo "◆ Initializing SQLite schema..."
rm -f matsya.db
python3 -c "
import sqlite3
conn = sqlite3.connect('matsya.db')
with open('schema.sql') as f:
    conn.executescript(f.read())
conn.commit()
cur = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name\")
tables = [row[0] for row in cur.fetchall()]
print(f'  Tables: {tables}')
conn.close()
"

# Create backlog so GATE sees work to do
echo "task from Manu" > backlog.txt

# Run state machine
echo ""
echo "◆ Running state machine..."
echo "(max_iterations=2, max_retries=2)"
python3 state_machine.py --config=config.json 2>&1

# Show results
echo ""
echo "◆ Output artifacts:"
ls -la output/ 2>/dev/null || echo "  (none)"
echo ""
echo "◆ Database tables populated:"
python3 -c "
import sqlite3
conn = sqlite3.connect('matsya.db')
for table in ['profiles', 'components', 'profile_components']:
    cur = conn.execute(f'SELECT COUNT(*) FROM {table}')
    print(f'  {table}: {cur.fetchone()[0]} rows')
conn.close()
"

# Cleanup
rm -f backlog.txt vasuki.signal
rm -rf signals output

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║  Run complete.                                     ║"
echo "╚════════════════════════════════════════════════════╝"
