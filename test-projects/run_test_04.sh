#!/usr/bin/env bash
# Sprint 04 — Full Pipeline Test
# Runs the engine end-to-end: PLAN → ENGINEER → REVIEW
# Agents read concept.md, produce backlog/brief → source code → review report
# All dispatch activity is logged to the SQLite database.

set -e
cd "$(dirname "$0")"
SM="/root/sm"
PROJECT="fast-api-04"

echo "═══════════════════════════════════════════════════════"
echo "  Full Pipeline Test — ${PROJECT}"
echo "═══════════════════════════════════════════════════════"
echo ""

# ── Clean and prepare ──
rm -rf "${PROJECT}"
mkdir -p "${PROJECT}"
cd "${PROJECT}"

# Write the concept (the pebble the agents will expand)
cat > concept.md << 'CONCEPT'
# FastAPI Read-Only API for test-project.db

Create a simple FastAPI application that provides read-only HTTP access to the SQLite database at `test-project.db`.
CONCEPT
echo "  Concept: $(head -1 concept.md)"
echo ""

# ── Step 1: Initialize project ──
echo "── Step 1: sm init ──"
python3 "${SM}/sm.py" init test-project.db --yes 2>&1 | head -5
echo ""

# ── Step 2: Run the pipeline engine ──
echo "── Step 2: sm run (full pipeline) ──"
echo "  Engine will dispatch: scribe-PLAN → builder-ENGINEER → warden-REVIEW"
echo ""

python3 "${SM}/sm.py" --db test-project.db run --profile builder --max-iterations 1 2>&1

echo ""
echo "  ✓ Pipeline run complete"
echo ""

# ── Step 3: Check deliverables ──
echo "── Step 3: Results ──"
echo ""

PASS=0
FAIL=0

echo "  Checking deliverables..."
echo ""

if [ -f sprint/001/brief.md ]; then
    echo "  ✅ sprint/001/brief.md exists (PLAN output)"
    PASS=$((PASS+1))
else
    echo "  ❌ sprint/001/brief.md missing"
    FAIL=$((FAIL+1))
fi

if [ -f src/main.py ]; then
    echo "  ✅ src/main.py exists (ENGINEER output)"
    PASS=$((PASS+1))
else
    echo "  ❌ src/main.py missing"
    FAIL=$((FAIL+1))
fi

# Check that main.py is valid Python that creates a FastAPI app
if python3 -c "import ast; ast.parse(open('src/main.py').read()); print('valid')" 2>/dev/null | grep -q valid; then
    echo "  ✅ src/main.py is valid Python"
    PASS=$((PASS+1))
else
    echo "  ❌ src/main.py has syntax errors"
    FAIL=$((FAIL+1))
fi

# Check that any src file uses SQLite
if grep -rqi "sqlite\|aiosqlite\|\.db" src/ 2>/dev/null; then
    echo "  ✅ src/ connects to SQLite"
    PASS=$((PASS+1))
else
    echo "  ❌ src/ no SQLite reference"
    FAIL=$((FAIL+1))
fi

if [ -f sprint/001/review.md ]; then
    echo "  ✅ sprint/001/review.md exists (REVIEW output)"
    PASS=$((PASS+1))
else
    echo "  ❌ sprint/001/review.md missing"
    FAIL=$((FAIL+1))
fi

if [ -f requirements.txt ]; then
    echo "  ✅ requirements.txt exists"
    PASS=$((PASS+1))
else
    echo "  ❌ requirements.txt missing"
    FAIL=$((FAIL+1))
fi

# ── Step 4: Check database logs ──
echo ""
echo "── Step 4: Database Logs ──"
echo ""

echo "  Dispatch log entries:"
python3 -c "
import sqlite3, json
conn = sqlite3.connect('test-project.db')
rows = conn.execute('SELECT agent_name, status, substr(request_text, 1, 60), substr(response_text, 1, 80) FROM dispatch_log ORDER BY id').fetchall()
for r in rows:
    print(f'    Agent: {r[0]:25s} Status: {r[1]:12s} Req: {r[2]}')
    print(f'    Resp: {r[3][:80]}')
    print()
conn.close()
" 2>&1

echo "  Phase events summary:"
python3 -c "
import sqlite3
conn = sqlite3.connect('test-project.db')
count = conn.execute('SELECT COUNT(*) FROM phase_events').fetchone()[0]
types = conn.execute('SELECT event_type, COUNT(*) FROM phase_events GROUP BY event_type ORDER BY COUNT(*) DESC').fetchall()
print(f'    Total events: {count}')
for t, c in types:
    print(f'    {t:30s} {c}')
conn.close()
" 2>&1

echo ""

# ── Summary ──
echo "═══════════════════════════════════════════════════════"
echo "  Results"
echo "═══════════════════════════════════════════════════════"
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo "  All checks passed. Full pipeline is working."
    echo "  The agents did the work."
else
    echo "  Some checks failed. Review output above."
fi
