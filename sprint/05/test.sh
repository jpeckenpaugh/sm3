#!/bin/bash
# Sprint 05 — Profile Cleanup & Tools Verification
# Run: bash sprint/05/test.sh

set -e

PASS=0
FAIL=0

pass() { PASS=$((PASS+1)); echo "  ✅ $1"; }
fail() { FAIL=$((FAIL+1)); echo "  ❌ $1"; }

echo "=== Sprint 05 Verification Suite ==="
echo ""

cd /root/sm
source .venv/bin/activate 2>/dev/null || true

# ─── 1. Seed order (ft029) ─────────────────────────────────────────────────
echo "--- 1. Seed Order (ft029) ---"
OUT=$(python3 -m genesis_sm.seed 2>&1)
WARNINGS=$(echo "$OUT" | grep -c "Base profile not found" || true)
if [ "$WARNINGS" -eq 0 ]; then
    pass "No 'Base profile not found' warnings during seed"
else
    fail "$WARNINGS base profile warnings still present"
fi
echo ""

# ─── 2. Zombie columns removed (ft026) ────────────────────────────────────
echo "--- 2. Zombie Columns Removed (ft026) ---"
COLS=$(sqlite3 matsya.db "PRAGMA table_info(profiles);" | cut -d'|' -f2)
if echo "$COLS" | grep -q "body"; then
    fail "'body' column still exists in profiles table"
else
    pass "'body' column removed from profiles table"
fi
if echo "$COLS" | grep -q "preamble"; then
    fail "'preamble' column still exists in profiles table"
else
    pass "'preamble' column removed from profiles table"
fi
echo ""

# ─── 3. Permission merge (ft024) ─────────────────────────────────────────
echo "--- 3. Permission Merge (ft024) ---"
python3 -m genesis_sm.cli --db matsya.db generate agents 2>&1 >/dev/null
if grep -q "search_files: allow" .opencode/agents/scribe-PLAN.md; then
    pass "scribe-PLAN inherits search_files from base"
else
    fail "scribe-PLAN missing search_files"
fi
if grep -q "list_files: allow" .opencode/agents/builder-ENGINEER.md; then
    pass "builder-ENGINEER inherits list_files from base"
else
    fail "builder-ENGINEER missing list_files"
fi
if grep -q "file_tree: allow" .opencode/agents/warden-GATE.md; then
    pass "warden-GATE inherits file_tree from base"
else
    fail "warden-GATE missing file_tree"
fi
if grep -q "read_pulse: allow" .opencode/agents/scribe-PLAN.md; then
    pass "scribe-PLAN has read_pulse from derived profile"
else
    fail "scribe-PLAN missing read_pulse"
fi
if grep -q "lint_code: allow" .opencode/agents/builder-ENGINEER.md; then
    pass "builder-ENGINEER has lint_code from derived profile"
else
    fail "builder-ENGINEER missing lint_code"
fi
if grep -q "compare_files: allow" .opencode/agents/warden-REVIEW.md; then
    pass "warden-REVIEW has compare_files from derived profile"
else
    fail "warden-REVIEW missing compare_files"
fi
echo ""

# ─── 4. Bootstrap protocol (ft025) ────────────────────────────────────────
echo "--- 4. Bootstrap Protocol (ft025) ---"
if grep -q "CONFIRM_BOOTSTRAP" .opencode/agents/scribe-PLAN.md; then
    pass "scribe-PLAN has CONFIRM_BOOTSTRAP section"
else
    fail "scribe-PLAN missing CONFIRM_BOOTSTRAP"
fi
if grep -q "Available MODE_FLAG values are CONFIRM_BOOTSTRAP, PLAN" .opencode/agents/scribe-PLAN.md; then
    pass "scribe-PLAN mode flag correctly substituted to PLAN"
else
    fail "scribe-PLAN mode flag not substituted"
fi
if grep -q "Available MODE_FLAG values are CONFIRM_BOOTSTRAP, SPRINT_GATE" .opencode/agents/warden-GATE.md; then
    pass "warden-GATE mode flag correctly substituted to SPRINT_GATE"
else
    fail "warden-GATE mode flag not substituted"
fi
# Verify no raw <MODE_FLAG> placeholders remain
REMAINING=$(grep -r "<MODE_FLAG>" .opencode/agents/*.md 2>/dev/null | wc -l || true)
if [ "$REMAINING" -eq 0 ]; then
    pass "No raw <MODE_FLAG> placeholders in any generated agent file"
else
    fail "$REMAINING raw <MODE_FLAG> placeholders remain"
fi
echo ""

# ─── 5. Auto-orientation in mode components ───────────────────────────────
echo "--- 5. Auto-Orientation ---"
for file in scribe-mode-plan scribe-mode-design scribe-mode-architect \
            scribe-mode-review scribe-mode-sprint-planning builder-mode-engineer \
            builder-mode-test warden-mode-review warden-mode-test-run warden-mode-gate; do
    if grep -q "file_tree" "components/prompts/${file}.json"; then
        pass "$file includes file_tree orientation"
    else
        fail "$file missing file_tree orientation"
    fi
done
echo ""

# ─── 6. sm generate agents (ft027) ────────────────────────────────────────
echo "--- 6. Generate All Agents (ft027) ---"
COUNT=$(ls .opencode/agents/*.md 2>/dev/null | wc -l)
ARCHIVE=$(ls .opencode/agents/archive/*.md 2>/dev/null | wc -l || true)
if [ "$COUNT" -ge 16 ]; then
    pass "sm generate agents produced $COUNT agent files (target: 16+)"
else
    fail "Only $COUNT agent files (expected 16+)"
fi
if [ "$ARCHIVE" -eq 5 ]; then
    pass "5 legacy agent files archived"
else
    fail "Expected 5 archived files, found $ARCHIVE"
fi
echo ""

# ─── 7. Universal tools work ─────────────────────────────────────────────
echo "--- 7. Universal Tools ---"
# search_files
OUT=$(bash scripts/search_files.sh "" 2>&1 || true)
if echo "$OUT" | grep -q "No pattern provided"; then
    pass "search_files validates empty pattern"
else
    fail "search_files missing validation"
fi
OUT=$(bash scripts/search_files.sh "def cmd_" --include "*.py" --max 3 2>&1)
if echo "$OUT" | grep -q '"matches"'; then
    pass "search_files returns structured JSON with matches"
else
    fail "search_files JSON invalid"
fi

# list_files
OUT=$(bash scripts/list_files.sh "backlog/*.md" --max 3 2>&1)
if echo "$OUT" | grep -q '"count"'; then
    pass "list_files returns structured JSON with count"
else
    fail "list_files JSON invalid"
fi

# file_tree
OUT=$(bash scripts/file_tree.sh --depth 2 --dirs-only 2>&1)
if echo "$OUT" | grep -q "backlog"; then
    pass "file_tree shows directory structure"
else
    fail "file_tree output empty"
fi
echo ""

# ─── 8. Domain tools work ────────────────────────────────────────────────
echo "--- 8. Domain Tools ---"
OUT=$(bash scripts/compare_files.sh README.md README.md --mode summary 2>&1)
if echo "$OUT" | grep -q '"identical": true'; then
    pass "compare_files correctly identifies identical files"
else
    fail "compare_files fails on identical files"
fi
OUT=$(bash scripts/lint_code.sh src/genesis_sm/cli.py 2>&1)
if echo "$OUT" | grep -q '"valid": true'; then
    pass "lint_code validates clean Python file"
else
    fail "lint_code fails on clean file"
fi
OUT=$(bash scripts/read_pulse.sh --db matsya.db 2>&1)
if echo "$OUT" | grep -q '"sprint_count"'; then
    pass "read_pulse returns sprint data"
else
    fail "read_pulse fails"
fi
echo ""

# ─── 9. Fleet dashboard files exist ──────────────────────────────────────
echo "--- 9. Fleet Dashboard ---"
if [ -f "ui/db.py" ] && [ -f "ui/main.py" ] && [ -f "ui/templates/base.html" ]; then
    pass "Dashboard files exist"
else
    fail "Dashboard files missing"
fi
if grep -q "set_active_db" "ui/db.py"; then
    pass "Dashboard has multi-DB config support"
else
    fail "Dashboard missing multi-DB support"
fi
echo ""

# ─── 10. pytest at init ──────────────────────────────────────────────────
echo "--- 10. Pytest at Init ---"
if grep -q "import pytest" "src/genesis_sm/cli.py"; then
    pass "sm init has pytest auto-install code"
else
    fail "sm init missing pytest check"
fi
echo ""

# ─── Summary ──────────────────────────────────────────────────────────────
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
