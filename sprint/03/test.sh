#!/usr/bin/env bash
# Sprint 03 — Automated Feature Tests
# Tests the DB-driven pipeline engine, events, contracts, escalation, and adoption.

set -e
cd "$(dirname "$0")/../.."  # project root

PASS=0
FAIL=0
TEST_DB="/tmp/sm3_test_$$.db"
SAMPLE_DIR="/tmp/sm3_sample_$$"

cleanup() {
    rm -f "$TEST_DB"
    rm -rf "$SAMPLE_DIR"
    rm -rf ".escalation"
}
trap cleanup EXIT

pass() { PASS=$((PASS+1)); echo "  ✅ $1"; }
fail() { FAIL=$((FAIL+1)); echo "  ❌ $1"; }

# ═══════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Sprint 03 — Automated Feature Tests"
echo "═══════════════════════════════════════════════════════"
echo ""

# ── ft001: Schema — 4 new tables ───────────────────────
echo "── ft001: Schema — pipeline tables ──"

# Create a fresh database and run schema
rm -f "$TEST_DB"
python3 -c "
import sqlite3
conn = sqlite3.connect('$TEST_DB')
with open('schema.sql') as f:
    conn.executescript(f.read())
conn.close()
"

# Check tables exist
for table in pipeline_states pipeline_transitions file_contracts phase_events; do
    python3 -c "
import sqlite3
conn = sqlite3.connect('$TEST_DB')
cursor = conn.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='$table'\")
assert cursor.fetchone() is not None, 'Table $table not found'
conn.close()
" && pass "$table table exists" || fail "$table table missing"
done

# Check phase_events index
python3 -c "
import sqlite3
conn = sqlite3.connect('$TEST_DB')
cursor = conn.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='index' AND name='idx_phase_events_sprint'\")
assert cursor.fetchone() is not None, 'Index not found'
conn.close()
" && pass "phase_events index exists" || fail "phase_events index missing"

echo ""

# ── ft002: seeds ───────────────────────────────────────
echo "── ft002: Pipeline seeds ──"

python3 -c "
import sqlite3
conn = sqlite3.connect('$TEST_DB')
from pipeline.seeds import seed_pipeline_tables
seed_pipeline_tables(conn)
conn.close()
" && pass "seed_pipeline_tables runs without error" || fail "seed_pipeline_tables failed"

python3 -c "
import sqlite3
conn = sqlite3.connect('$TEST_DB')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM pipeline_states')
assert cursor.fetchone()[0] == 5, 'Expected 5 states'
cursor.execute('SELECT COUNT(*) FROM pipeline_transitions')
assert cursor.fetchone()[0] == 6, 'Expected 6 transitions'
cursor.execute('SELECT COUNT(*) FROM file_contracts')
count = cursor.fetchone()[0]
assert count >= 9, f'Expected >=9 contracts, got {count}'
conn.close()
" && pass "seed data correct (5 states, 6 transitions, 9+ contracts)" || fail "seed data incorrect"

echo ""

# ── ft003: phase_events table + reader ─────────────────
echo "── ft003: Phase events (ft015) ──"

# Seed the full database first
python3 seed.py --db "$TEST_DB" > /dev/null 2>&1

# Create a test sprint
python3 -c "
import sqlite3, json
conn = sqlite3.connect('$TEST_DB')
conn.execute(\"INSERT INTO sprints (number, mode, status, started_at) VALUES (999, 'driven', 'active', '2026-07-08T00:00:00Z')\")
conn.commit()
sid = conn.execute('SELECT id FROM sprints WHERE number = 999').fetchone()[0]

# Log some events
from pipeline.events import log_phase_event, read_phase_events
log_phase_event(conn, sid, 'PLAN', 1, 1, 'phase_start', 'Entering PLAN')
log_phase_event(conn, sid, 'PLAN', 1, 1, 'phase_script_start', 'scripts/phase_plan.sh')
log_phase_event(conn, sid, 'PLAN', 1, 1, 'phase_script_exit', 'exit_code=0')
log_phase_event(conn, sid, 'PLAN', 1, 1, 'phase_end', 'passed')

# Read them back
events = read_phase_events(conn, sid)
assert len(events) == 4, f'Expected 4 events, got {len(events)}'
conn.close()
print('OK')
" && pass "log_phase_event and read_phase_events work" || fail "phase events CRUD failed"

python3 -c "
import sqlite3, json
conn = sqlite3.connect('$TEST_DB')
sid = conn.execute('SELECT id FROM sprints WHERE number = 999').fetchone()[0]
from pipeline.events import read_phase_events
events = read_phase_events(conn, sid, as_json=True)
assert isinstance(events, list), 'Expected list'
assert len(events) == 4, f'Expected 4 events, got {len(events)}'
assert 'event_type' in events[0], 'Missing event_type key'
conn.close()
print('OK')
" && pass "read_phase_events as_json=True works" || fail "JSON events format incorrect"

echo ""

# ── ft004: pipeline engine transition logic ────────────
echo "── ft004: Engine — transition resolution ──"

python3 -c "
import sqlite3
conn = sqlite3.connect('$TEST_DB')
from pipeline.engine import _load_states, _load_transitions, _evaluate_guard, _advance

states = _load_states(conn)
transitions = _load_transitions(conn)

name_to_id = {s['name']: s['id'] for s in states}
id_to_name = {s['id']: s['name'] for s in states}

# Test: PLAN should advance to WRITE
result = _advance('PLAN', transitions, name_to_id, id_to_name, {})
assert result == 'WRITE', f'Expected WRITE, got {result}'

# Test: GATE with backlog_exists → should advance to PLAN
result = _advance('GATE', transitions, name_to_id, id_to_name, {'backlog_file': 'backlog'})
assert result == 'PLAN', f'Expected PLAN (backlog exists), got {result}'

# Test: GATE with backlog_empty → should be terminal
import os
result = _advance('GATE', transitions, name_to_id, id_to_name, {'backlog_file': '/dev/null'})
assert result is None, f'Expected None (terminal), got {result}'

conn.close()
print('OK')
" && pass "transition resolution correct" || fail "transition resolution failed"

echo ""

# ── ft005: guard evaluation ────────────────────────────
echo "── ft005: Engine — guard evaluation ──"

python3 -c "
from pipeline.engine import _evaluate_guard

assert _evaluate_guard('', {}) == True, 'Empty guard should match'
assert _evaluate_guard('true', {}) == True, '\"true\" should match'
assert _evaluate_guard('backlog_exists', {'backlog_file': '/tmp'}) == True
assert _evaluate_guard('backlog_empty', {'backlog_file': '/dev/null'}) == True
assert _evaluate_guard('max_iterations_reached', {'iteration': 5, 'max_iterations': 3}) == True
assert _evaluate_guard('max_iterations_reached', {'iteration': 2, 'max_iterations': 5}) == False
assert _evaluate_guard('tests_passed', {'tests_passed': True}) == True
assert _evaluate_guard('tests_passed', {'tests_passed': False}) == False
assert _evaluate_guard('unknown_guard', {}) == False, 'Unknown guard should not match'
print('OK')
" && pass "guard evaluation correct" || fail "guard evaluation failed"

echo ""

# ── ft006: contract verification ───────────────────────
echo "── ft006: File contracts (ft012) ──"

rm -rf "$SAMPLE_DIR"
mkdir -p "$SAMPLE_DIR/sprint/01"
touch "$SAMPLE_DIR/sprint/01/brief.md"

python3 -c "
import sqlite3, os, sys
_root = os.path.abspath('.')
os.chdir('$SAMPLE_DIR')
sys.path.insert(0, _root)
conn = sqlite3.connect('$TEST_DB')

from pipeline.engine import _verify_contracts, _write_contract_manifest

# Verify contracts for PLAN (which outputs sprint/*/brief.md)
results = _verify_contracts(conn, 'PLAN', 999, 1, 1)
assert len(results) >= 1, f'Expected at least 1 contract, got {len(results)}'
# brief.md should exist (we created it)
brief_results = [r for r in results if 'brief.md' in r['pattern']]
assert len(brief_results) > 0, 'brief.md contract not found'

# Test manifest writing (writes to CWD which is now $SAMPLE_DIR)
_write_contract_manifest('PLAN', 1, results)
manifest_path = os.path.join(os.getcwd(), 'sprint/1/.contracts/plan.json')
assert os.path.exists(manifest_path), f'Manifest not written to {manifest_path}'

conn.close()
print('OK')
" && pass "contract verification and manifest writing work" || fail "contract verification failed"

echo ""

# ── ft007: escalation detection ────────────────────────
echo "── ft007: Escalation mechanism (ft013) ──"

mkdir -p ".escalation/PLAN"
echo "Ambiguous specification: the backlog requirement conflicts with the brief." > ".escalation/PLAN/ambiguous-scope.md"

python3 -c "
from pipeline.engine import _check_escalations
result = _check_escalations('PLAN')
assert result is not None, 'Should detect escalation file'
assert 'ambiguous-scope' in result['file'], 'Wrong escalation file detected'
assert 'Ambiguous specification' in result['content'], 'Wrong content'

# Clean state should return None
import os
os.remove('.escalation/PLAN/ambiguous-scope.md')
os.rmdir('.escalation/PLAN')
result = _check_escalations('PLAN')
assert result is None, 'Should return None when no escalation files exist'
print('OK')
" && pass "escalation detection works" || fail "escalation detection failed"

echo ""

# ── ft008: state_machine.py dispatch ───────────────────
echo "── ft008: Backward compatibility ──"

# Test: _has_pipeline_tables returns True for seeded DB
python3 -c "
import sys
sys.path.insert(0, '.')
from state_machine import _has_pipeline_tables
result = _has_pipeline_tables('$TEST_DB')
assert result == True, f'Expected True for seeded DB, got {result}'
print('OK')
" && pass "_has_pipeline_tables detects pipeline schema" || fail "pipeline table detection failed"

# Test: _has_pipeline_tables returns False for DB without pipeline tables
python3 -c "
import sqlite3, sys, os
sys.path.insert(0, '.')
no_pipe_db = '${TEST_DB}_nopipe'
# Create a DB with only old tables
conn = sqlite3.connect(no_pipe_db)
conn.execute('CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY, name TEXT)')
conn.close()
from state_machine import _has_pipeline_tables
result = _has_pipeline_tables(no_pipe_db)
assert result == False, f'Expected False for DB without pipeline tables, got {result}'
os.unlink(no_pipe_db)
print('OK')
" && pass "_has_pipeline_tables returns False for old DB" || fail "pipeline table detection false positive"

echo ""

# ═══════════════════════════════════════════════════════
echo "═══════════════════════════════════════════════════════"
echo "  Results"
echo "═══════════════════════════════════════════════════════"
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo "  All tests passed. Sprint 03 is verified."
else
    echo "  Some tests failed. Review output above."
    exit 1
fi
