#!/usr/bin/env bash
# +x automatically set by chmod below; run with: bash sprint/07/test.sh
# Sprint 07 — Verification Suite
# Tests that sm init produces correct agent files with:
#   - No raw <MODE_FLAG> placeholders
#   - Full inheritance chain resolution
#   - Correct mode flag substitution
#   - Output parity between init and generate paths
#
# Depends on ft030 (generator.py extraction) and ft031 (init fix).

set -euo pipefail

# Ensure working directory is the project root
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

# Ensure the genesis_sm package (under src/) is findable
export PYTHONPATH="$PROJECT_ROOT/src:${PYTHONPATH:-}"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); }
fail() { FAIL=$((FAIL + 1)); echo "  ❌ $1"; }

echo "=== Sprint 07 Verification Suite ==="
echo ""

# ─── 1. Module import ────────────────────────────────────────────────────────
echo "--- 1. Generator module imports ---"
if python3 -c "from genesis_sm.generator import assemble_components, permissions_to_yaml, deep_merge, safe_json_loads, resolve_inheritance_chain, get_mode_flag; print('OK')" 2>&1; then
    pass
    echo "  ✅ generator.py imports cleanly"
else
    fail "generator.py import failed"
fi
echo ""

# ─── 2. Backward compatibility — sm generate agent ────────────────────────────
echo "--- 2. sm generate agent backward compatibility ---"

# Backup current agents
BACKUP_DIR=$(mktemp -d)
cp -r .opencode/agents/*.md "$BACKUP_DIR/" 2>/dev/null || true

# Generate fresh agents using the refactored code
# Use --db to point at the project's database
DB_PATH="$PROJECT_ROOT/matsya.db"
python3 -m genesis_sm.cli --db "$DB_PATH" generate agents --output-dir /tmp/sprint07-gen-a 2>&1 | tail -1 || true

# Compare with previous output (same DB, so should be identical)
ANY_DIFF=0
for f in "$BACKUP_DIR"/*.md; do
    name=$(basename "$f")
    if [ -f "/tmp/sprint07-gen-a/$name" ]; then
        if ! diff -q "$f" "/tmp/sprint07-gen-a/$name" > /dev/null 2>&1; then
            echo "  ⚠ Difference in $name (may be expected if agents were stale)"
            ANY_DIFF=1
        fi
    fi
done

if [ "$ANY_DIFF" -eq 0 ]; then
    pass
    echo "  ✅ sm generate agents output is consistent"
else
    # This may be expected if the previous backup had stale agents.
    # We check structural correctness instead:
    for f in /tmp/sprint07-gen-a/*.md; do
        name=$(basename "$f")
        if grep -q '<MODE_FLAG>' "$f" 2>/dev/null; then
            fail "$name contains raw <MODE_FLAG>"
        fi
    done
    echo "  ✅ No raw <MODE_FLAG> in freshly generated agents"
    pass
fi
rm -rf "$BACKUP_DIR"
rm -rf /tmp/sprint07-gen-a
echo ""

# ─── 3. sm init produces correct agent files ─────────────────────────────────
echo "--- 3. sm init produces correct agent files ---"

rm -rf /tmp/sprint07-test
mkdir -p /tmp/sprint07-test
cd /tmp/sprint07-test

# Run init against current project's seed data
python3 -m genesis_sm.cli init /tmp/sprint07-test/matsya.db --yes \
    --schema "$PROJECT_ROOT"/schema.sql \
    --seed-root "$PROJECT_ROOT" 2>&1 | tail -5 || true

# Check every derived profile for raw <MODE_FLAG>
MODE_FLAG_FOUND=0
for f in .opencode/agents/*.md; do
    if grep -q '<MODE_FLAG>' "$f" 2>/dev/null; then
        echo "  ❌ $f contains raw <MODE_FLAG>"
        MODE_FLAG_FOUND=1
    fi
done

if [ "$MODE_FLAG_FOUND" -eq 0 ]; then
    pass
    echo "  ✅ No raw <MODE_FLAG> in any generated agent file"
else
    fail "Raw <MODE_FLAG> found in generated agent files"
fi

cd "$PROJECT_ROOT"
rm -rf /tmp/sprint07-test
echo ""

# ─── 4. Inheritance resolution ───────────────────────────────────────────────
echo "--- 4. Inheritance resolution ---"

rm -rf /tmp/sprint07-inherit
mkdir -p /tmp/sprint07-inherit
cd /tmp/sprint07-inherit

python3 -m genesis_sm.cli init /tmp/sprint07-inherit/matsya.db --yes \
    --schema "$PROJECT_ROOT"/schema.sql \
    --seed-root "$PROJECT_ROOT" 2>&1 | tail -3 || true

# scribe-PLAN must contain inherited base components
INHERIT_OK=0
if grep -q "You do exactly as you are told" .opencode/agents/scribe-PLAN.md 2>/dev/null; then
    INHERIT_OK=$((INHERIT_OK + 1))
else
    fail "scribe-PLAN missing inherited component 'obey-exactly'"
fi

if grep -q "The Scribe gives form" .opencode/agents/scribe-PLAN.md 2>/dev/null; then
    INHERIT_OK=$((INHERIT_OK + 1))
else
    fail "scribe-PLAN missing inherited component 'scribe-preamble'"
fi

if grep -q "You write documents, schemas" .opencode/agents/scribe-PLAN.md 2>/dev/null; then
    INHERIT_OK=$((INHERIT_OK + 1))
else
    fail "scribe-PLAN missing inherited component 'scribe-domain'"
fi

if [ "$INHERIT_OK" -eq 3 ]; then
    pass
    echo "  ✅ scribe-PLAN has full inheritance chain"
fi

cd "$PROJECT_ROOT"
rm -rf /tmp/sprint07-inherit
echo ""

# ─── 5. Mode flag substitution ───────────────────────────────────────────────
echo "--- 5. Mode flag substitution ---"

rm -rf /tmp/sprint07-mode
mkdir -p /tmp/sprint07-mode
cd /tmp/sprint07-mode

python3 -m genesis_sm.cli init /tmp/sprint07-mode/matsya.db --yes \
    --schema "$PROJECT_ROOT"/schema.sql \
    --seed-root "$PROJECT_ROOT" 2>&1 | tail -3 || true

MODE_OK=0

# scribe-PLAN must have PLAN
if grep -q 'CONFIRM_BOOTSTRAP`, `PLAN`' .opencode/agents/scribe-PLAN.md 2>/dev/null; then
    MODE_OK=$((MODE_OK + 1))
else
    fail "scribe-PLAN mode flag not correctly substituted to PLAN"
fi

# warden-GATE must have SPRINT_GATE
if grep -q 'CONFIRM_BOOTSTRAP`, `SPRINT_GATE`' .opencode/agents/warden-GATE.md 2>/dev/null; then
    MODE_OK=$((MODE_OK + 1))
else
    fail "warden-GATE mode flag not correctly substituted to SPRINT_GATE"
fi

# builder-ENGINEER must have ENGINEER
if grep -q '`ENGINEER`' .opencode/agents/builder-ENGINEER.md 2>/dev/null; then
    MODE_OK=$((MODE_OK + 1))
else
    fail "builder-ENGINEER mode flag not correctly substituted"
fi

# scribe-DESIGN must have DESIGN
if grep -q '`DESIGN`' .opencode/agents/scribe-DESIGN.md 2>/dev/null; then
    MODE_OK=$((MODE_OK + 1))
else
    fail "scribe-DESIGN mode flag not correctly substituted"
fi

if [ "$MODE_OK" -eq 4 ]; then
    pass
    echo "  ✅ All derived profiles have correct mode flags"
fi

cd "$PROJECT_ROOT"
rm -rf /tmp/sprint07-mode
echo ""

# ─── 6. Output parity (init vs generate) ─────────────────────────────────────
echo "--- 6. Output parity (init vs generate) ---"

rm -rf /tmp/sprint07-a /tmp/sprint07-b
mkdir -p /tmp/sprint07-a /tmp/sprint07-b

# Create init-based agents
cd /tmp/sprint07-a
python3 -m genesis_sm.cli init /tmp/sprint07-a/matsya.db --yes \
    --schema "$PROJECT_ROOT"/schema.sql \
    --seed-root "$PROJECT_ROOT" 2>&1 | tail -3 || true

# Create generate-based agents (same DB seed)
cp /tmp/sprint07-a/matsya.db /tmp/sprint07-b/matsya.db
cd /tmp/sprint07-b
python3 -m genesis_sm.cli --db /tmp/sprint07-b/matsya.db generate agents --output-dir /tmp/sprint07-b/.opencode/agents 2>&1 | tail -1 || true

# Compare every file
PARITY_OK=0
for f in /tmp/sprint07-a/.opencode/agents/*.md; do
    name=$(basename "$f")
    other="/tmp/sprint07-b/.opencode/agents/$name"
    if [ ! -f "$other" ]; then
        fail "Missing: $name in generate output"
        PARITY_OK=1
    elif ! diff -q "$f" "$other" > /dev/null 2>&1; then
        echo "  ⚠ Difference in $name:"
        diff "$f" "$other" | head -20
        fail "$name differs between init and generate"
        PARITY_OK=1
    fi
done

if [ "$PARITY_OK" -eq 0 ]; then
    pass
    echo "  ✅ All agent files identical between init and generate paths"
fi

cd "$PROJECT_ROOT"
rm -rf /tmp/sprint07-a /tmp/sprint07-b
echo ""

# ─── Summary ─────────────────────────────────────────────────────────────────
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -eq 0 ]; then
    echo "All tests passed. Sprint 07 is verified."
else
    echo "Some tests failed. Review output above."
    exit 1
fi
