#!/bin/bash
# Sprint 06 — Profile Power Tools Verification
# Run: bash sprint/06/test.sh

set -e

PASS=0
FAIL=0

pass() { PASS=$((PASS+1)); echo "  ✅ $1"; }
fail() { FAIL=$((FAIL+1)); echo "  ❌ $1"; }

echo "=== Sprint 06 Verification Suite ==="
echo ""

cd /root/sm
source .venv/bin/activate 2>/dev/null || true

# ─── 1. ft009 — Component Params ──────────────────────────────────────────
echo "--- 1. Component Params (ft009) ---"
# Check that params column is fetched in assembly query
if grep -q "pc.params" src/genesis_sm/cli.py; then
    pass "_assemble_components_for_profiles fetches params column"
else
    fail "params column not in assembly query"
fi
# Check that {{ key }} substitution is implemented
if grep -q "{{ " src/genesis_sm/cli.py; then
    pass "Template param substitution ({{ key }}) is wired"
else
    fail "Template param substitution missing"
fi
# Check that params can be set and read
sqlite3 matsya.db "UPDATE profile_components SET params = '{\"mode\":\"PLAN\"}' WHERE id = 1"
READBACK=$(sqlite3 matsya.db "SELECT params FROM profile_components WHERE id = 1")
if echo "$READBACK" | grep -q "PLAN"; then
    pass "Params column read/write works"
else
    fail "Params column read/write failed"
fi
echo ""

# Kill any lingering proxy from previous runs
pkill -f "proxy.py" 2>/dev/null || true

# ─── 2. ft017 — Webbfetch Proxy ──────────────────────────────────────────
echo "--- 2. Webbfetch Proxy (ft017) ---"
if [ -f "scripts/proxy.py" ]; then
    pass "proxy.py exists"
else
    fail "proxy.py missing"
fi
if [ -f "scripts/proxy-allow-list.json" ]; then
    pass "proxy-allow-list.json exists"
else
    fail "proxy-allow-list.json missing"
fi
# Start proxy, test health, test blocked, test allowed, stop proxy
_PROXY_PORT=8095
_PROXY_PID=""
cleanup_proxy() {
    if [ -n "$_PROXY_PID" ]; then
        kill $_PROXY_PID 2>/dev/null || true
        wait $_PROXY_PID 2>/dev/null || true
    fi
}
trap cleanup_proxy EXIT
python3 scripts/proxy.py --port $_PROXY_PORT >/dev/null 2>&1 &
_PROXY_PID=$!
sleep 2
HEALTH=$(curl -s http://localhost:$_PROXY_PORT/ 2>/dev/null)
if echo "$HEALTH" | grep -q '"ok"'; then
    pass "Proxy health check returns OK"
else
    fail "Proxy health check failed"
fi
BLOCKED=$(curl -s -X POST -d '{"url":"https://example.com"}' http://localhost:$_PROXY_PORT/ 2>/dev/null)
if echo "$BLOCKED" | grep -q "not allowed"; then
    pass "Proxy blocks example.com (403)"
else
    fail "Proxy failed to block example.com"
fi
ALLOWED=$(curl -s --max-time 5 -X POST -d '{"url":"https://docs.python.org/3/"}' http://localhost:$_PROXY_PORT/ 2>/dev/null)
if echo "$ALLOWED" | grep -q '"status": 200'; then
    pass "Proxy allows docs.python.org (200)"
else
    fail "Proxy failed to allow docs.python.org"
fi
cleanup_proxy
trap - EXIT
echo ""

# ─── 3. ft010 — Profile Export/Import ────────────────────────────────────
echo "--- 3. Profile Export/Import (ft010) ---"
sm --db matsya.db profile export --output /tmp/s06-test-export.json 2>&1 >/dev/null
if [ -f /tmp/s06-test-export.json ]; then
    pass "sm profile export creates output file"
else
    fail "sm profile export did not create file"
fi
EXPORT_COUNT=$(python3 -c "import json; d=json.load(open('/tmp/s06-test-export.json')); print(len(d['profiles']))" 2>/dev/null)
if [ "$EXPORT_COUNT" -ge 16 ]; then
    pass "Exported $EXPORT_COUNT profiles (expected 16+)"
else
    fail "Only exported $EXPORT_COUNT profiles"
fi
IMPORT_OUT=$(sm --db matsya.db profile import --input /tmp/s06-test-export.json 2>&1)
if echo "$IMPORT_OUT" | grep -q "Imported"; then
    pass "sm profile import succeeds"
else
    fail "sm profile import failed"
fi
rm -f /tmp/s06-test-export.json
echo ""

# ─── 4. ft008 — Variant Creation ─────────────────────────────────────────
echo "--- 4. Variant Creation (ft008) ---"
# Clean up any previous test variant
sqlite3 matsya.db "DELETE FROM profiles WHERE name = 'test-variant'; DELETE FROM components WHERE name = 'scribe-mode-test_mode'; DELETE FROM profile_components WHERE profile_id NOT IN (SELECT id FROM profiles)" 2>/dev/null || true
VAR_OUT=$(timeout 10 sm --db matsya.db profile variant --base scribe --name test-variant --mode TEST_MODE --prompt "In TEST_MODE mode, you test things." 2>&1) || VAR_OUT="$VAR_OUT (timeout)"
if echo "$VAR_OUT" | grep -q "created"; then
    pass "sm profile variant creates new profile"
else
    fail "sm profile variant failed"
fi
if [ -f ".opencode/agents/test-variant.md" ]; then
    pass "Variant agent file generated"
else
    fail "Variant agent file not generated"
fi
# Verify the mode flag works
if grep -q "TEST_MODE" .opencode/agents/test-variant.md; then
    pass "Variant has correct mode flag"
else
    fail "Variant missing mode flag"
fi
# Clean up
rm -f .opencode/agents/test-variant.md
sqlite3 matsya.db "DELETE FROM profiles WHERE name = 'test-variant'; DELETE FROM components WHERE name = 'scribe-mode-test_mode'; DELETE FROM profile_components WHERE profile_id NOT IN (SELECT id FROM profiles)"
echo ""

# ─── 5. ft007 fix — Duplicate numbering ──────────────────────────────────
echo "--- 5. ft007 Fix ---"
if [ -f "backlog/ft007b-profile-inheritance.md" ]; then
    pass "Renamed file ft007b-profile-inheritance.md exists"
else
    fail "ft007b file missing"
fi
if [ ! -f "backlog/ft007-profile-inheritance.md" ]; then
    pass "Old ft007-profile-inheritance.md removed"
else
    fail "Old ft007 file still exists"
fi
echo ""

# ─── 6. New commands in CLI help ─────────────────────────────────────────
echo "--- 6. CLI Commands ---"
sm profile --help 2>&1 | grep -q "export"
if [ $? -eq 0 ]; then
    pass "sm profile export command available"
else
    fail "sm profile export missing"
fi
sm profile --help 2>&1 | grep -q "import"
if [ $? -eq 0 ]; then
    pass "sm profile import command available"
else
    fail "sm profile import missing"
fi
sm profile --help 2>&1 | grep -q "variant"
if [ $? -eq 0 ]; then
    pass "sm profile variant command available"
else
    fail "sm profile variant missing"
fi
echo ""

# ─── Summary ──────────────────────────────────────────────────────────────
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
