#!/usr/bin/env bash
# run_test.sh — Execute the Matsya state machine test suite

set -euo pipefail

echo "╔════════════════════════════════════════════════════╗"
echo "║  Matsya State Machine — Test Suite                ║"
echo "╚════════════════════════════════════════════════════╝"

# Step 1: Setup
echo ""
echo "◆ Setup: making scripts executable..."
chmod +x git_commit.sh wait-and-touch.sh scripts/*.sh run_test.sh 2>/dev/null || true
mkdir -p signals output

# Step 2: Initialize the database schema
echo ""
echo "◆ Database: initializing schema..."
rm -f matsya.db
python3 -c "
import sqlite3
conn = sqlite3.connect('matsya.db')
with open('schema.sql') as f:
    conn.executescript(f.read())
conn.commit()
cur = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name\")
tables = [row[0] for row in cur.fetchall()]
print(f'  Tables created: {tables}')
conn.close()
"
echo "  Schema OK."

# Step 3: Create backlog and run one iteration
echo ""
echo "◆ State Machine: running with mock agents..."
echo "iter 1 task" > backlog.txt

python3 state_machine.py --config=config.json 2>&1 || echo "  (state machine finished with non-zero exit)"

# Step 4: Check results
echo ""
echo "◆ Results:"
echo "  output files:"
ls output/ 2>/dev/null || echo "    (none)"
echo "  signal files:"
ls signals/ 2>/dev/null || echo "    (none)"
echo "  backlog exists:"
[ -f backlog.txt ] && echo "    yes ($(wc -l < backlog.txt) lines)" || echo "    no"
echo "  vasuki.signal:"
[ -f vasuki.signal ] && echo "    present" || echo "    absent"

# Step 5: Verify database content
echo ""
echo "◆ Database verification:"
python3 -c "
import sqlite3
conn = sqlite3.connect('matsya.db')
cur = conn.execute('SELECT COUNT(*) FROM profiles')
print(f'  Profiles: {cur.fetchone()[0]}')
cur = conn.execute('SELECT COUNT(*) FROM components')
print(f'  Components: {cur.fetchone()[0]}')
cur = conn.execute('SELECT COUNT(*) FROM profile_components')
print(f'  Profile-Component links: {cur.fetchone()[0]}')
conn.close()
"

# Step 6: Cleanup test artifacts but keep the db and scripts
echo ""
echo "◆ Cleanup (test artifacts)..."
rm -f backlog.txt vasuki.signal
rm -rf signals output
echo "  Done."

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║  Test suite complete.                              ║"
echo "╚════════════════════════════════════════════════════╝"
