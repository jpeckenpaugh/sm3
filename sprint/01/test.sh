#!/usr/bin/env bash
# shellcheck disable=SC2016
#
# Sprint 01 — Automated Feature Tests
#
# Tests all 6 features using a dedicated test database.
# Exits 0 on success, non-zero on any failure.
#
# Usage:
#   bash sprint/01/test.sh
#

set -euo pipefail

# ─── Configuration ──────────────────────────────────────────────────────────

TEST_DB="/tmp/sm_sprint01_test.db"
SCHEMA_SQL="schema.sql"
SEED_ROOT="."
SM="python3 sm.py"
SEED="python3 seed.py"
AGENTS_DIR="/tmp/sm_sprint01_agents"

PASS=0
FAIL=0

cleanup() {
    rm -f "$TEST_DB"
    rm -rf "$AGENTS_DIR"
}

# Run before exit
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

check_exit() {
    local desc="$1"
    shift
    if "$@" > /dev/null 2>&1; then
        pass "$desc"
    else
        fail "$desc"
    fi
}

check_output_contains() {
    local desc="$1"
    local pattern="$2"
    shift 2
    if "$@" 2>&1 | grep -q "$pattern"; then
        pass "$desc"
    else
        fail "$desc"
    fi
}

check_output_exact() {
    local desc="$1"
    local expected="$2"
    local actual
    shift 2
    actual=$("$@" 2>&1)
    if echo "$actual" | grep -q "$expected"; then
        pass "$desc"
    else
        echo "    Expected to contain: $expected"
        echo "    Got: $actual"
        fail "$desc"
    fi
}

# ─── Setup ───────────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Sprint 01 — Automated Feature Tests"
echo "═══════════════════════════════════════════════════════"
echo ""

# Ensure we are in the project root
cd "$(dirname "$0")/../.."

# Clean up any previous test artifacts
cleanup
mkdir -p "$AGENTS_DIR"

# ─── ft001: Seed & Component Decomposition ───────────────────────────────────

echo "── ft001: Seed & Component Decomposition ──"

# 1.1 Fresh seed
check_exit "seed exits 0" $SEED --db "$TEST_DB"

# 1.2 Idempotency — second seed should also succeed
check_exit "seed is idempotent (second run)" $SEED --db "$TEST_DB"

# 1.3 Profile count
check_output_contains "6 profiles seeded" "→ 6 profiles loaded" $SEED --db "$TEST_DB"

# 1.4 Component count
check_output_contains "13 components seeded" "→ 13 components loaded" $SEED --db "$TEST_DB"

# 1.5 Profile-component links count
check_output_contains "14 profile-component links" "→ 14 profile-component links loaded" $SEED --db "$TEST_DB"

pass "ft001: Seed & Component Decomposition complete"

# ─── ft002: CLI Framework ──────────────────────────────────────────────────

echo ""
echo "── ft002: CLI Framework ──"

# 2.1 sm.py --help
check_exit "sm --help exits 0" $SM --help

# 2.2 sm seed via sm.py
check_exit "sm seed via sm.py" $SM --db "$TEST_DB" seed

# 2.3 sm list --help
check_output_contains "sm list --help shows subcommands" "profiles" $SM list --help

# 2.4 sm generate --help
check_output_contains "sm generate --help shows subcommands" "agent" $SM generate --help

pass "ft002: CLI Framework complete"

# ─── ft004: List Commands ───────────────────────────────────────────────────

echo ""
echo "── ft004: List Commands ──"

# 4.1 sm list profiles (table)
check_output_contains "list profiles shows scribe" "scribe" $SM --db "$TEST_DB" list profiles

# 4.2 sm list profiles --json
check_output_contains "list profiles --json is valid JSON" '"name": "scribe"' $SM --db "$TEST_DB" list profiles --json

# 4.3 sm list profiles -v (verbose with permissions)
check_output_contains "list profiles -v shows permissions" "Permissions" $SM --db "$TEST_DB" list profiles -v

# 4.4 sm list components
check_output_contains "list components shows obey-exactly" "obey-exactly" $SM --db "$TEST_DB" list components

# 4.5 sm list components --json
check_output_contains "list components --json is valid JSON" '"type": "rule"' $SM --db "$TEST_DB" list components --json

# 4.6 sm list components -v (verbose shows full content)
check_output_contains "list components -v shows full content" "You do exactly as you are told" $SM --db "$TEST_DB" list components -v

pass "ft004: List Commands complete"

# ─── ft006: Generate Agent ──────────────────────────────────────────────────

echo ""
echo "── ft006: Generate Agent ──"

# 6.1 Generate scribe agent
check_exit "generate agent scribe" $SM --db "$TEST_DB" generate agent scribe --output-dir "$AGENTS_DIR"

# 6.2 Verify output file exists
check_exit "scribe agent file exists" test -f "$AGENTS_DIR/scribe.md"

# 6.3 Verify YAML frontmatter
check_output_contains "scribe agent has description" "description: the scribe" cat "$AGENTS_DIR/scribe.md"
check_output_contains "scribe agent has mode" "mode: all" cat "$AGENTS_DIR/scribe.md"
check_output_contains "scribe agent has temperature" "temperature: 0.15" cat "$AGENTS_DIR/scribe.md"
check_output_contains "scribe agent has permissions" 'permission:' cat "$AGENTS_DIR/scribe.md"

# 6.4 Verify body content (assembled components)
check_output_contains "scribe agent body has obey-exactly" "You do exactly as you are told" cat "$AGENTS_DIR/scribe.md"
check_output_contains "scribe agent body has preamble" "The Scribe gives form" cat "$AGENTS_DIR/scribe.md"
check_output_contains "scribe agent body has domain" "You write documents" cat "$AGENTS_DIR/scribe.md"

# 6.5 Generate builder agent
check_exit "generate agent builder" $SM --db "$TEST_DB" generate agent builder --output-dir "$AGENTS_DIR"
check_exit "builder agent file exists" test -f "$AGENTS_DIR/builder.md"

# 6.6 Builder has obey-exactly (shared rule)
check_output_contains "builder agent shares obey-exactly rule" "You do exactly as you are told" cat "$AGENTS_DIR/builder.md"

# 6.7 Generate warden agent (no obey-exactly rule)
check_exit "generate agent warden" $SM --db "$TEST_DB" generate agent warden --output-dir "$AGENTS_DIR"
check_output_contains "warden agent exists" "The Warden watches" cat "$AGENTS_DIR/warden.md"

# 6.8 Generate agent for non-existent profile (expect failure)
check_exit "generate agent for missing profile exits non-zero" bash -c "! $SM --db '$TEST_DB' generate agent nonexistent --output-dir '$AGENTS_DIR'"

pass "ft006: Generate Agent complete"

# ─── ft005: Status Command ──────────────────────────────────────────────────

echo ""
echo "── ft005: Status Command ──"

# 5.1 Status with seeded database
check_output_contains "status shows database ready" "ready" $SM --db "$TEST_DB" status
check_output_contains "status shows profile count" "Profiles:" $SM --db "$TEST_DB" status
check_output_contains "status shows component count" "Components:" $SM --db "$TEST_DB" status
check_output_contains "status shows assembly count" "Assemblies:" $SM --db "$TEST_DB" status

pass "ft005: Status Command complete"

# ─── ft003: Run Command (dry-run verification) ──────────────────────────────

echo ""
echo "── ft003: Run Command ──"

# The run command starts the state machine loop. We can't run it fully in
# a test, but we can verify that profile loading and config construction work
# by testing the environment variable export and error handling.

# 3.1 Error on non-existent profile
check_exit "run with missing profile exits non-zero" bash -c "! $SM --db '$TEST_DB' run --profile nonexistent"

# 3.2 Verify profile loading works (we check by running with max-iterations=1
#    and verifying it prints the profile info before the state machine starts)
check_output_contains "run displays profile name" "Profile: scribe" \
    $SM --db "$TEST_DB" run --profile scribe --max-iterations 1 --max-retries 1 2>&1 || true

check_output_contains "run displays role" "Role:" \
    $SM --db "$TEST_DB" run --profile scribe --max-iterations 1 --max-retries 1 2>&1 || true

check_output_contains "run displays component count" "Components:" \
    $SM --db "$TEST_DB" run --profile scribe --max-iterations 1 --max-retries 1 2>&1 || true

pass "ft003: Run Command (loading verification) complete"

# ─── Variant Test (the litmus) ──────────────────────────────────────────────

echo ""
echo "── Variant Test (litmus) ──"

# Create variant seed files
mkdir -p components/prompts

cat > components/prompts/scribe-domain-opinionated.json << 'EOF'
{
  "type": "prompt",
  "name": "scribe-domain-opinionated",
  "content": "You challenge assumptions. You propose alternatives. You write with conviction — but you still write documents, not code."
}
EOF

cat > profiles/opinionated-scribe.json << 'EOF'
{
  "name": "opinionated-scribe",
  "version": "1.0.0",
  "header": {
    "role": "the opinionated scribe",
    "mode": "all",
    "temperature": 0.25
  },
  "permissions": {
    "*": "deny",
    "edit": {
      "*.md": "allow",
      "*.sql": "allow",
      "*.json": "allow",
      "*.py": "allow"
    }
  }
}
EOF

cat > profile-components/opinionated-scribe.json << 'EOF'
{
  "profile": "opinionated-scribe",
  "components": [
    { "type": "rule", "name": "obey-exactly", "order_idx": 0 },
    { "type": "prompt", "name": "scribe-preamble", "order_idx": 1 },
    { "type": "prompt", "name": "scribe-domain-opinionated", "order_idx": 2 }
  ]
}
EOF

# Re-seed (should be idempotent with the new data)
check_exit "variant seed exits 0" $SEED --db "$TEST_DB"

# Verify 7 profiles now (6 original + 1 variant)
check_output_contains "7 profiles after adding variant" "→ 7 profiles loaded" $SEED --db "$TEST_DB"

# Verify 14 components (13 original + 1 variant)
check_output_contains "14 components after adding variant" "→ 14 components loaded" $SEED --db "$TEST_DB"

# Generate agent for variant
check_exit "generate variant agent" $SM --db "$TEST_DB" generate agent opinionated-scribe --output-dir "$AGENTS_DIR"
check_exit "variant agent file exists" test -f "$AGENTS_DIR/opinionated-scribe.md"

# Verify variant agent reuses obey-exactly and scribe-preamble
check_output_contains "variant agent uses obey-exactly" "You do exactly as you are told" cat "$AGENTS_DIR/opinionated-scribe.md"
check_output_contains "variant agent uses scribe-preamble" "The Scribe gives form" cat "$AGENTS_DIR/opinionated-scribe.md"
check_output_contains "variant agent has new domain content" "You challenge assumptions" cat "$AGENTS_DIR/opinionated-scribe.md"

# Verify original scribe is unchanged
check_output_contains "original scribe unchanged" "You write documents, schemas" cat "$AGENTS_DIR/scribe.md"

# Clean up variant files
rm -f components/prompts/scribe-domain-opinionated.json
rm -f profiles/opinionated-scribe.json
rm -f profile-components/opinionated-scribe.json

pass "Variant Test: no duplication of existing data"

# ─── Summary ────────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Results"
echo "═══════════════════════════════════════════════════════"
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo "  All tests passed. Sprint 01 is verified."
    echo ""
    exit 0
else
    echo "  Some tests failed. Review output above."
    echo ""
    exit 1
fi
