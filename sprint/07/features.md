# Sprint 07 — Features

*Kill the duplication. Three features, strict dependency order. Build in this sequence.*

---

| # | Feature | Source | Depends on |
|---|---------|--------|------------|
| 1 | **ft030 — Extract shared agent generator module** | `backlog/ft030-extract-agent-generator.md` | — |
| 2 | **ft031 — Fix `cmd_init()` agent generation** | `backlog/ft031-fix-init-agent-generation.md` | ft030 |
| 3 | **ft032 — Verify `sm init` generation** | `backlog/ft032-verify-init-generation.md` | ft031 |

---

## Dependency Rationale

### Step 1 — ft030: Extract generator module

Foundation. The six helper functions (`deep_merge`, `safe_json_loads`, `resolve_inheritance_chain`, `get_mode_flag`, `assemble_components`, `permissions_to_yaml`) must exist in their own module before any code path can import them.

This step is a pure extraction. No behavioural change. The test for this step is: `sm generate agent scribe-PLAN` produces identical output before and after the change.

### Step 2 — ft031: Fix cmd_init()

Depends on ft030 because the fix replaces the inline loop with calls to `generator.py`.

This step eliminates the duplicated ~45 lines in `cmd_init()` (currently lines 1163–1207) and replaces them with correct calls to `resolve_inheritance_chain()` and `assemble_components()`.

The test for this step is: `sm init --db /tmp/test.db --yes` produces agent files with:
- No literal `<MODE_FLAG>` strings
- Full inheritance chain (base components present)
- Correct mode flags (PLAN, ENGINEER, SPRINT_GATE, etc.)

### Step 3 — ft032: Test and verify

Creates the test script that proves the fix works and prevents regression. Compares output of `sm init` vs `sm generate agents` for every profile — they must be identical.

---

## Build Order

```
1. ft030 — Extract generator.py ───────── created from cli.py lines 504–638
       │
2. ft031 — Fix cmd_init() ────────────── replace lines 1163–1207
       │
3. ft032 — Write test.sh ────────────── run parity tests
```

---

## First Working Path

1. Create `src/genesis_sm/generator.py` with the six extracted functions
2. Import them in `cli.py`, remove the old private definitions, update all call sites
3. Run `sm generate agents` and verify output is identical to a backup taken before the change
4. Replace the inline generation loop in `cmd_init()` with calls to `generator.py`
5. Delete the old duplicated ~45 lines
6. Run `sm init --db /tmp/test.db --yes` and verify agent files are correct
7. Write `sprint/07/test.sh` and run it
8. Write results to `sprint/07/test-results.md`

---

## Test Strategy

| Check | Method |
|-------|--------|
| No regression in `sm generate agent` | Compare file contents before/after ft030 |
| No `<MODE_FLAG>` in `sm init` output | `grep -r '<MODE_FLAG>' .opencode/agents/` |
| Full inheritance in `sm init` output | grep for base components in derived agent files |
| Parity between init and generate | `diff -r` both output directories |

---

## Reference Documents

- `backlog/ft030-extract-agent-generator.md`
- `backlog/ft031-fix-init-agent-generation.md`
- `backlog/ft032-verify-init-generation.md`
- `sprint/07/brief.md`

---

*Written by Saraswati. Built by Matsya. Watched by Kurma. One generator to rule them all.*
