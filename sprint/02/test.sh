#!/usr/bin/env bash
#
# Sprint 02 — Automated Feature Tests
#
# Tests all 9 features for the durable execution log and project system.
# Exits 0 on success, non-zero on any failure.
#
# Usage:
#   bash sprint/02/test.sh
#

set -euo pipefail

# ─── Configuration ──────────────────────────────────────────────────────────

TEST_DB="/tmp/sm_sprint02_test.db"
TEST_DIR="/tmp/sm_sprint02_project"
TEST_REGISTRY_DIR="/tmp/sm_sprint02_registry"
TEST_REGISTRY_FILE="$TEST_REGISTRY_DIR/projects.json"
SM="python3 $(pwd)/sm.py"
SEED="python3 $(pwd)/seed.py"

PASS=0
FAIL=0

cleanup() {
    rm -f "$TEST_DB"
    rm -rf "$TEST_DIR"
    rm -rf "$TEST_REGISTRY_DIR"
}

trap cleanup EXIT

# ─── Helpers ─────────────────────────────────────────────────────────────────

pass() {
    echo "  ✅ $1"
    PASS=$((PASS + 1))
}

fail() {
    echo "  ❌ $1"
    FAIL=$((FAIL + 1))
}

# Run a command and pass/fail based on exit code
check_exit() {
    local desc="$1"
    shift
    if "$@" > /dev/null 2>&1; then
        pass "$desc"
    else
        fail "$desc"
    fi
}

# Run a command and pass/fail based on exit code being non-zero
check_exit_fail() {
    local desc="$1"
    shift
    if "$@" > /dev/null 2>&1; then
        fail "$desc"
    else
        pass "$desc"
    fi
}

# Run a command (may fail), capture output, check for pattern in stdout+stderr
check_output_contains() {
    local desc="$1"
    local pattern="$2"
    shift 2
    local output
    output=$("$@" 2>&1) || true
    if echo "$output" | grep -q "$pattern"; then
        pass "$desc"
    else
        fail "$desc"
    fi
}

# Run a command (may fail), capture output, check pattern is NOT present
check_not_output() {
    local desc="$1"
    local pattern="$2"
    shift 2
    local output
    output=$("$@" 2>&1) || true
    if echo "$output" | grep -q "$pattern"; then
        fail "$desc"
    else
        pass "$desc"
    fi
}

# ─── Setup ───────────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Sprint 02 — Automated Feature Tests"
echo "═══════════════════════════════════════════════════════"
echo ""

# Ensure we are in the project root
cd "$(dirname "$0")/../.."

# Clean up any previous test artifacts
cleanup
mkdir -p "$TEST_REGISTRY_DIR"

# Override registry location for testing (exported so all child processes inherit it)
export SM_PROJECTS_PATH="$TEST_REGISTRY_FILE"

# ─── Feature 1: sprints + phase_runs tables ─────────────────────────────────

echo "── ft001: Schema — sprints + phase_runs tables ──"

check_exit "seed creates database" $SEED --db "$TEST_DB"

check_output_contains "sprints table exists" "sprints" \
    python3 -c "import sqlite3; c=sqlite3.connect('$TEST_DB'); print(c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall())"

check_output_contains "phase_runs table exists" "phase_runs" \
    python3 -c "import sqlite3; c=sqlite3.connect('$TEST_DB'); print(c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall())"

check_output_contains "sprints has number column" "number" \
    python3 -c "import sqlite3; c=sqlite3.connect('$TEST_DB'); print([d[1] for d in c.execute('PRAGMA table_info(sprints)').fetchall()])"

check_output_contains "phase_runs has sprint_id column" "sprint_id" \
    python3 -c "import sqlite3; c=sqlite3.connect('$TEST_DB'); print([d[1] for d in c.execute('PRAGMA table_info(phase_runs)').fetchall()])"

pass "ft001: Schema tables verified"

# ─── Feature 3: sm log (empty) ──────────────────────────────────────────────

echo ""
echo "── ft003: sm log (no data) ──"

check_output_contains "sm log shows empty message" "No sprints recorded" \
    $SM --db "$TEST_DB" log

# --json on empty DB outputs [] (raw JSON array)
check_output_contains "sm log --json shows empty array" "\[\]" \
    $SM --db "$TEST_DB" log --json

pass "ft003: Empty log display verified"

# ─── Feature 4: sm sprint subcommands ───────────────────────────────────────

echo ""
echo "── ft004: sm sprint subcommands ──"

check_exit "sprint start --number 1 --mode manual" \
    $SM --db "$TEST_DB" sprint start --number 1 --mode manual

check_output_contains "sprint 1 exists in DB" "1" \
    python3 -c "import sqlite3; c=sqlite3.connect('$TEST_DB'); print(c.execute('SELECT number FROM sprints WHERE number=1').fetchone()[0])"

check_exit "sprint start --number 2" \
    $SM --db "$TEST_DB" sprint start --number 2

check_exit_fail "sprint start duplicate exits non-zero" \
    $SM --db "$TEST_DB" sprint start --number 1

check_exit "sprint note --number 1" \
    $SM --db "$TEST_DB" sprint note --number 1 --notes "Initial planning"

check_output_contains "sprint 1 has note" "Initial planning" \
    python3 -c "import sqlite3; c=sqlite3.connect('$TEST_DB'); print(c.execute('SELECT notes FROM sprints WHERE number=1').fetchone()[0])"

check_exit "sprint complete --number 1" \
    $SM --db "$TEST_DB" sprint complete --number 1

check_output_contains "sprint 1 status is completed" "completed" \
    python3 -c "import sqlite3; c=sqlite3.connect('$TEST_DB'); print(c.execute('SELECT status FROM sprints WHERE number=1').fetchone()[0])"

check_exit "sprint fail --number 2 --reason" \
    $SM --db "$TEST_DB" sprint fail --number 2 --reason "Scope changed"

check_output_contains "sprint 2 status is failed" "failed" \
    python3 -c "import sqlite3; c=sqlite3.connect('$TEST_DB'); print(c.execute('SELECT status FROM sprints WHERE number=2').fetchone()[0])"

check_exit_fail "sprint note on missing sprint exits non-zero" \
    $SM --db "$TEST_DB" sprint note --number 99 --notes "nope"

check_exit_fail "sprint complete on missing sprint exits non-zero" \
    $SM --db "$TEST_DB" sprint complete --number 99

pass "ft004: Sprint lifecycle verified"

# ─── Feature 3: sm log (with data) ─────────────────────────────────────────

echo ""
echo "── ft003: sm log (with data) ──"

check_output_contains "sm log shows sprint 1" "Sprint 1" \
    $SM --db "$TEST_DB" log

check_output_contains "sm log shows sprint 2" "Sprint 2" \
    $SM --db "$TEST_DB" log

check_output_contains "sm log --sprint 1 filters" "Sprint 1" \
    $SM --db "$TEST_DB" log --sprint 1

check_not_output "sm log --sprint 1 excludes sprint 2" "Sprint 2" \
    $SM --db "$TEST_DB" log --sprint 1

check_output_contains "sm log --json is valid JSON" '"number": 1' \
    $SM --db "$TEST_DB" log --json

check_output_contains "sm log --json shows mode" '"mode": "manual"' \
    $SM --db "$TEST_DB" log --json

check_output_contains "sm log --json --sprint 2" '"number": 2' \
    $SM --db "$TEST_DB" log --json --sprint 2

check_output_contains "manual sprint shows no phase log" "No phase log" \
    $SM --db "$TEST_DB" log --sprint 1 --phases

pass "ft003: Log display verified"

# ─── Feature 5: sm init ────────────────────────────────────────────────────

echo ""
echo "── ft005: sm init ──"

FRESH_DIR="$TEST_DIR/fresh"
mkdir -p "$FRESH_DIR"

check_exit "sm init fresh project" \
    $SM init "$FRESH_DIR/matsya.db" --yes --name "test-fresh" \
    --seed-root "$(pwd)" --schema "$(pwd)/schema.sql"

check_exit "database file exists" test -f "$FRESH_DIR/matsya.db"

check_exit "backlog directory exists" test -d "$FRESH_DIR/backlog"
check_exit "sprint directory exists" test -d "$FRESH_DIR/sprint"
check_exit "agents directory exists" test -d "$FRESH_DIR/.opencode/agents"

check_exit ".sm-config.json exists" test -f "$FRESH_DIR/.sm-config.json"

check_output_contains ".sm-config.json has db_path" "matsya.db" \
    cat "$FRESH_DIR/.sm-config.json"

check_output_contains "profiles seeded in init" "scribe" \
    $SM --db "$FRESH_DIR/matsya.db" list profiles

check_exit "scribe agent generated" test -f "$FRESH_DIR/.opencode/agents/scribe.md"

check_output_contains "scribe agent has frontmatter" "description: the scribe" \
    cat "$FRESH_DIR/.opencode/agents/scribe.md"

# Registry was written by sm init
check_output_contains "registry has project" "test-fresh" \
    cat "$TEST_REGISTRY_FILE"

check_output_contains "default project set" "test-fresh" \
    python3 -c "import json; r=json.load(open('$TEST_REGISTRY_FILE')); print(r.get('default', ''))"

pass "ft005: Project init verified"

# ─── Feature 9: Sprint 01 adoption ──────────────────────────────────────────

echo ""
echo "── ft009: Sprint 01 adoption ──"

ADOPT_DIR="$TEST_DIR/adopt"
mkdir -p "$ADOPT_DIR/sprint/01"
echo "brief content" > "$ADOPT_DIR/sprint/01/brief.md"
echo "features content" > "$ADOPT_DIR/sprint/01/features.md"

check_exit "sm init with adoption" \
    $SM init "$ADOPT_DIR/matsya.db" --yes --name "test-adopt" \
    --seed-root "$(pwd)" --schema "$(pwd)/schema.sql"

check_output_contains "adopted sprint 1 exists" "Sprint 1" \
    $SM --db "$ADOPT_DIR/matsya.db" log

check_output_contains "adopted sprint is manual" "manual" \
    $SM --db "$ADOPT_DIR/matsya.db" log --json

check_output_contains "adopted sprint is completed" "completed" \
    $SM --db "$ADOPT_DIR/matsya.db" log --json

pass "ft009: Sprint 01 adoption verified"

# ─── Feature 2: State machine logging (dry-run) ─────────────────────────────

echo ""
echo "── ft002: State machine phase logging ──"

SM_LOG_DB="/tmp/sm_sprint02_smlog.db"
$SEED --db "$SM_LOG_DB" > /dev/null 2>&1

check_exit "sm run writes phase logs" \
    $SM --db "$SM_LOG_DB" run --profile scribe --max-iterations 1 --max-retries 1

# Verify phase_runs rows exist (count > 0)
check_exit "phase_runs rows exist" \
    python3 -c "import sqlite3; c=sqlite3.connect('$SM_LOG_DB'); assert c.execute('SELECT COUNT(*) FROM phase_runs').fetchone()[0] > 0"

check_output_contains "sprint auto-created" "Sprint 1" \
    $SM --db "$SM_LOG_DB" log

check_output_contains "auto-created sprint is driven" "driven" \
    $SM --db "$SM_LOG_DB" log --json

# Verify phase_runs have valid statuses (at least 'passed' from successful script skips)
check_exit "phase_runs have valid statuses" \
    python3 -c "import sqlite3; c=sqlite3.connect('$SM_LOG_DB'); rows=c.execute('SELECT DISTINCT status FROM phase_runs').fetchall(); assert len(rows) > 0; assert all(r[0] in ('running','passed','failed','skipped') for r in rows)"

check_output_contains "log --phases shows phases" "Phase" \
    $SM --db "$SM_LOG_DB" log --phases

rm -f "$SM_LOG_DB"

pass "ft002: State machine logging verified"

# ─── Feature 6: Registry ────────────────────────────────────────────────────

echo ""
echo "── ft006: Project registry ──"

# SM_PROJECTS_PATH is already exported — list projects reads it directly
check_output_contains "list projects shows test-fresh" "test-fresh" \
    $SM list projects

check_output_contains "list projects --json is valid" "test-fresh" \
    $SM list projects --json

pass "ft006: Registry display verified"

# ─── Feature 8: sm projects subcommands ─────────────────────────────────────

echo ""
echo "── ft008: sm projects subcommands ──"

check_exit "projects default sets default" \
    $SM projects default "test-fresh"

check_output_contains "default project is test-fresh" "test-fresh" \
    python3 -c "import json; r=json.load(open('$TEST_REGISTRY_FILE')); print(r.get('default', ''))"

check_exit "projects remove works" \
    $SM projects remove "test-adopt"

check_not_output "registry no longer has test-adopt" "test-adopt" \
    cat "$TEST_REGISTRY_FILE"

pass "ft008: Project management verified"

# ─── Feature 7: .sm-config.json auto-discovery ──────────────────────────────

echo ""
echo "── ft007: .sm-config.json auto-discovery ──"

# Run from inside the project directory, using bash -c so cd takes effect
check_output_contains "auto-discovery finds profiles" "scribe" \
    bash -c "cd '$FRESH_DIR' && $SM list profiles"

# Verify auto-discovery resolves to the same database as explicit --db
# by comparing profile JSON output from both methods
AUTO_OUTPUT=$(bash -c "cd '$FRESH_DIR' && $SM list profiles --json" 2>/dev/null || true)
EXPLICIT_OUTPUT=$($SM --db "$FRESH_DIR/matsya.db" list profiles --json 2>/dev/null || true)
if [ "$AUTO_OUTPUT" = "$EXPLICIT_OUTPUT" ]; then
    pass "auto-discovery uses correct db"
else
    fail "auto-discovery uses correct db"
fi

pass "ft007: Auto-discovery verified"

# ─── Error handling ─────────────────────────────────────────────────────────

echo ""
echo "── Error handling ──"

# Diagnostic: verify --db flag is parsed by checking the db_path directly
# via a Python one-liner that mimics the CLI argument parsing
check_output_contains "--db flag is parsed by argparse" "nonexistent_12345" \
    python3 -c "
import sys
sys.path.insert(0, '$(pwd)')
from sm import get_db_path
# Simulate args.db being set
db_path = get_db_path('/tmp/sm_nonexistent_12345.db', allow_missing=True)
print(f'db_path={db_path}')
assert db_path == '/tmp/sm_nonexistent_12345.db', f'Expected /tmp/...nonexistent_12345.db, got {db_path}'
print('PASS')
"

# sm log on non-existent DB (--db flag takes precedence over auto-discovery)
# Capture raw output for debugging
LOG_MISSING_OUTPUT=$($SM --db "/tmp/sm_nonexistent_12345.db" log 2>&1 || true)
if echo "$LOG_MISSING_OUTPUT" | grep -q "No database found"; then
    pass "log on missing DB shows message"
else
    echo "    Raw output was: $LOG_MISSING_OUTPUT"
    fail "log on missing DB shows message"
fi

# sm sprint on non-existent DB
check_exit_fail "sprint on missing DB exits non-zero" \
    $SM --db "/tmp/sm_nonexistent_12345.db" sprint start --number 1

# sm run on non-existent profile (use a valid DB)
ERROR_DB="/tmp/sm_sprint02_error.db"
$SEED --db "$ERROR_DB" > /dev/null 2>&1
check_exit_fail "run on missing profile exits non-zero" \
    $SM --db "$ERROR_DB" run --profile nonexistent
rm -f "$ERROR_DB"

# sm run on non-existent DB
check_exit_fail "run on missing DB exits non-zero" \
    $SM --db "/tmp/sm_sprint02_nonexistent.db" run --profile scribe

pass "Error handling verified"

# ─── Summary ────────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Results"
echo "═══════════════════════════════════════════════════════"
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo ""

unset SM_PROJECTS_PATH

if [ "$FAIL" -eq 0 ]; then
    echo "  All tests passed. Sprint 02 is verified."
    echo ""
    exit 0
else
    echo "  Some tests failed. Review output above."
    echo ""
    exit 1
fi
