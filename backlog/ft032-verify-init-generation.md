# ft032 — Verify `sm init` Agent Generation

**Feature:** Write a test script that verifies `sm init` produces correct agent files with full inheritance resolution, `<MODE_FLAG>` substitution, and component params applied.

---

## Motivation

The Sprint 05 test suite (`sprint/05/test-results.md`) included a test "No raw `<MODE_FLAG>` placeholders in any generated agent file" but only exercised the `sm generate agents` path. The `sm init` path was never tested, which is why the bug survived into Sprint 06.

This feature creates a dedicated test that exercises both paths and compares their output, preventing regression.

---

## Test Script

Create `sprint/07/test.sh` that:

### 1. Test `sm init` produces correct agent files

```bash
# Create a temporary project
rm -rf /tmp/sprint07-test
mkdir -p /tmp/sprint07-test
cd /tmp/sprint07-test

# Run init against current project's seed data
sm init /tmp/sprint07-test/matsya.db --yes \
  --schema /root/sm/schema.sql \
  --seed-root /root/sm

# Check every derived profile for raw <MODE_FLAG>
for f in .opencode/agents/*.md; do
    if grep -q '<MODE_FLAG>' "$f"; then
        echo "❌ $f contains raw <MODE_FLAG>"
        exit 1
    fi
done
echo "✅ No raw <MODE_FLAG> in any generated agent file"
```

### 2. Test inheritance resolution

```bash
# scribe-PLAN must contain inherited base components
grep -q "obey-exactly" .opencode/agents/scribe-PLAN.md || {
    echo "❌ scribe-PLAN missing inherited component 'obey-exactly'"
    exit 1
}
grep -q "The Scribe gives form" .opencode/agents/scribe-PLAN.md || {
    echo "❌ scribe-PLAN missing inherited component 'scribe-preamble'"
    exit 1
}
grep -q "You write documents, schemas" .opencode/agents/scribe-PLAN.md || {
    echo "❌ scribe-PLAN missing inherited component 'scribe-domain'"
    exit 1
}
echo "✅ scribe-PLAN has full inheritance chain"
```

### 3. Test mode flag substitution

```bash
# scribe-PLAN must have PLAN, not <MODE_FLAG>
grep -q "All prompts must start with one of the following MODE_FLAG strings: \`CONFIRM_BOOTSTRAP\`, \`PLAN\`" \
    .opencode/agents/scribe-PLAN.md || {
    echo "❌ scribe-PLAN mode flag not correctly substituted to PLAN"
    exit 1
}

# warden-GATE must have SPRINT_GATE
grep -q "All prompts must start with one of the following MODE_FLAG strings: \`CONFIRM_BOOTSTRAP\`, \`SPRINT_GATE\`" \
    .opencode/agents/warden-GATE.md || {
    echo "❌ warden-GATE mode flag not correctly substituted to SPRINT_GATE"
    exit 1
}

# builder-ENGINEER must have ENGINEER
grep -q "\`ENGINEER\`" .opencode/agents/builder-ENGINEER.md || {
    echo "❌ builder-ENGINEER mode flag not correctly substituted"
    exit 1
}
echo "✅ All derived profiles have correct mode flags"
```

### 4. Test output parity between `sm init` and `sm generate agents`

```bash
# Create init-based agents
rm -rf /tmp/sprint07-a && mkdir -p /tmp/sprint07-a
cd /tmp/sprint07-a
sm init /tmp/sprint07-a/matsya.db --yes \
  --schema /root/sm/schema.sql --seed-root /root/sm

# Create generate-based agents (same DB seed)
rm -rf /tmp/sprint07-b && mkdir -p /tmp/sprint07-b
cp /tmp/sprint07-a/matsya.db /tmp/sprint07-b/matsya.db
cd /tmp/sprint07-b
sm generate agents --output-dir /tmp/sprint07-b/.opencode/agents

# Compare every file
for f in /tmp/sprint07-a/.opencode/agents/*.md; do
    name=$(basename "$f")
    other="/tmp/sprint07-b/.opencode/agents/$name"
    if [ ! -f "$other" ]; then
        echo "❌ Missing: $name in generate output"
        exit 1
    fi
    if ! diff -q "$f" "$other" > /dev/null 2>&1; then
        echo "❌ Difference in $name between init and generate"
        diff "$f" "$other"
        exit 1
    fi
done
echo "✅ All agent files identical between init and generate paths"
```

### 5. Cleanup

```bash
rm -rf /tmp/sprint07-test /tmp/sprint07-a /tmp/sprint07-b
echo "✅ Cleanup complete"
```

---

## Test Results File

Run the test script and write results to `sprint/07/test-results.md` in the same format as previous sprints:

```
=== Sprint 07 Verification Suite ===

--- 1. sm init produces correct agent files ---
  ✅ No raw <MODE_FLAG> in any generated agent file

--- 2. Inheritance resolution ---
  ✅ scribe-PLAN has full inheritance chain

--- 3. Mode flag substitution ---
  ✅ scribe-PLAN mode flag correctly substituted to PLAN
  ✅ warden-GATE mode flag correctly substituted to SPRINT_GATE
  ✅ builder-ENGINEER mode flag correctly substituted to ENGINEER

--- 4. Output parity (init vs generate) ---
  ✅ All agent files identical between init and generate paths

=== Results: X passed, 0 failed ===
```

---

## Files Changed

| File | Change |
|------|--------|
| `sprint/07/test.sh` | **Created** — test script |
| `sprint/07/test-results.md` | **Created** — test results |

---

*Specified by Saraswati. Built by Matsya. Watched by Kurma.*
