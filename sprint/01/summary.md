# Sprint 01 — Engineer Summary

*Built by the Engineer. Reviewed by the Warden. Shipped by Matsya.*

---

## What Was Built

Six features, implemented in dependency order, using Python standard library only.

### ft001 — Seed & Component Decomposition

**Files created:**
- `profiles/` — 6 JSON files (scribe, builder, warden, origin, courier, keeper)
- `components/rules/obey-exactly.json` — shared behavioral rule
- `components/prompts/` — 12 JSON files (preamble + domain for each profile)
- `profile-components/` — 6 JSON files defining ordered component assembly per profile
- `seed.py` — reads seed data and upserts into SQLite database

**Key decisions:**
- `profile-components/*.json` references components by `(type, name)` pair, resolved at seed time
- `preamble` and `body` fields omitted from seed files (assembled from components at query time)
- Missing component references produce a warning but do not halt seeding
- Idempotent — safe to re-run; uses `ON CONFLICT` for upserts

### ft002 — CLI Framework

**Files created:**
- `sm.py` — single file, argparse-based command dispatch

**Commands implemented:**
| Command | Purpose |
|---------|---------|
| `sm seed` | Populate database from seed files |
| `sm run --profile <name>` | Load profile, assemble components, start state machine loop |
| `sm list profiles` | Display profiles (table or `--json`) |
| `sm list components` | Display components (table or `--json`) |
| `sm status` | Show database state, backlog, signal, iteration |
| `sm generate agent <name>` | Render profile as `.opencode/agents/<name>.md` |

### ft003 — Run Command

**Implementation:**
- `sm run --profile scribe` queries `profiles`, assembles components via `profile_components` join, builds a config dict, and calls `state_machine.run_with_config(cfg)`
- Sets environment variables for phase scripts: `MATSYA_PROFILE`, `MATSYA_HEADER`, `MATSYA_PERMISSIONS`, `MATSYA_BODY`
- CLI flags (`--max-iterations`, `--max-retries`) override `config.json` values

**Refactoring:**
- `state_machine.py` gained `run_with_config(cfg)` — a programmatic entry point that accepts a config dict directly
- Existing `main()` delegates to `run_with_config()` — fully backward compatible

### ft004 — List Commands

**Implementation:**
- `sm list profiles` — column-aligned table: Name, Version, Role, Mode, Temperature
- `sm list profiles -v` — adds Permissions column
- `sm list profiles --json` — raw JSON output
- `sm list components` — Type, Name, Content Preview (truncated at 60 chars)
- `sm list components -v` — full content display
- `sm list components --json` — raw JSON output
- No external dependencies; hand-rolled column formatting

### ft005 — Status Command

**Implementation:**
- Checks: database existence, profile/component/assembly counts, backlog directory/file, signal file, iteration state file (`matsya_state.json`), active profile from `MATSYA_PROFILE` env var
- Graceful "Never run" output when no state exists

### ft006 — Generate Agent Command

**Implementation:**
- `sm generate agent scribe` — queries profile + components, renders OpenCode agent markdown
- YAML frontmatter: `description` from `header.role`, `mode`, `temperature`, `permissions`
- Body: components concatenated in `order_idx` sequence, separated by blank lines
- Hand-rolled JSON-to-YAML converter (no PyYAML dependency) — quotes keys with special characters (`*`, `?`, `&`, etc.)
- Output to `.opencode/agents/<name>.md` (configurable via `--output-dir`)

---

## How to Test

### 1. Fresh seed

```bash
# Remove any existing test database
rm -f test_matsya.db

# Seed the database
python3 seed.py --db test_matsya.db

# Expected output: 6 profiles, 13 components, 12 profile-component links loaded
```

### 2. Verify via list commands

```bash
# Via seed.py directly
python3 seed.py --db test_matsya.db

# Via sm.py
python3 sm.py --db test_matsya.db seed
python3 sm.py --db test_matsya.db list profiles
python3 sm.py --db test_matsya.db list components
```

Expected profiles output (table):

```
Name                  Version   Role                       Mode    Temperature
────────────────────   ────────   ───────────────────────   ────    ───────────
builder               1.0.0      the builder               all     0.2
courier               1.0.0      the courier               all     0.1
keeper                1.0.0      the keeper                all     0.1
origin                1.0.0      the origin                all     0.3
scribe                1.0.0      the scribe                all     0.15
warden                1.0.0      the warden                all     0.1
```

Expected components output (table):

```
Type       Name                          Content Preview
──────     ──────────────────────────     ────────────────────────────────────────────────
prompt     builder-domain                You write code, tests, and deployment scripts...
prompt     builder-preamble              The Builder receives specifications and produces...
prompt     courier-domain                You relay what you receive. You do not modify. You...
prompt     courier-preamble              The Courier carries signals between phases...
prompt     keeper-domain                 You receive. You index. You archive. You do not...
prompt     keeper-preamble               The Keeper preserves the cargo after the flood...
prompt     origin-domain                 You hold the intention. You drop the pebble. You...
prompt     origin-preamble               The Origin is the human operator. Root authority.
prompt     scribe-domain                 You write documents, schemas, and handoff...
prompt     scribe-preamble               The Scribe gives form to intention before it...
prompt     warden-domain                 You observe and reflect. You do not create...
prompt     warden-preamble               The Warden watches. The Warden does not write.
rule       obey-exactly                  You do exactly as you are told. No more, and no...
```

### 3. Verify JSON output

```bash
python3 sm.py --db test_matsya.db list profiles --json
python3 sm.py --db test_matsya.db list components --json
```

### 4. Verify status (before and after seed)

```bash
# Before seed (no database)
python3 sm.py status

# After seed
python3 sm.py --db test_matsya.db status
```

### 5. Generate an agent file

```bash
python3 sm.py --db test_matsya.db generate agent scribe
cat .opencode/agents/scribe.md
```

Expected output:

```markdown
---
description: the scribe
mode: all
temperature: 0.15
permission:
  "*": deny
  edit:
    "*.md": allow
    "*.sql": allow
    "*.json": allow
---

You do exactly as you are told. No more, and no less.

The Scribe gives form to intention before it becomes implementation.

You write documents, schemas, and handoff specifications. You do not write executable code.
```

### 6. Idempotency test

```bash
# Run seed twice — should produce identical results
python3 seed.py --db test_matsya.db
python3 seed.py --db test_matsya.db

# Component counts should be the same
python3 sm.py --db test_matsya.db list components --json | python3 -c "import sys,json; print(len(json.load(sys.stdin)))"
# Expected: 13
```

### 7. Variant test (the litmus)

Create a variant by adding three files, then re-seed:

```bash
# 1. New component
cat > components/prompts/scribe-domain-opinionated.json << 'EOF'
{
  "type": "prompt",
  "name": "scribe-domain-opinionated",
  "content": "You challenge assumptions. You propose alternatives. You write with conviction — but you still write documents, not code."
}
EOF

# 2. New profile
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

# 3. New assembly (reuses obey-exactly and scribe-preamble)
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

# Re-seed
python3 seed.py --db test_matsya.db

# Verify
python3 sm.py --db test_matsya.db list profiles --json | python3 -c "import sys,json; profiles=json.load(sys.stdin); print([p['name'] for p in profiles])"
# Expected: ['builder', 'courier', 'keeper', 'opinionated-scribe', 'origin', 'scribe', 'warden']

# Generate agent file for the variant
python3 sm.py --db test_matsya.db generate agent opinionated-scribe
cat .opencode/agents/opinionated-scribe.md
```

---

## Existing Code That Was Not Changed

- `state_machine.py` — `main()` still works exactly as before; `run_with_config()` was added alongside it
- `config.json` — format unchanged; still loadable by `state_machine.py`
- `scripts/` — all phase scripts untouched
- `.opencode/agents/` — existing agent files remain until `sm generate agent` overwrites them

---

## Architecture Notes

**Data flow:**
```
Seed files (JSON) → seed.py → SQLite DB
                                    ↓
                             sm.py (argparse dispatch)
                           /    |    |    |    \
                     seed  run  list status  generate
                                    ↓
                          state_machine.run_with_config()
```

**Module dependencies:**
- `sm.py` imports `seed` (for `seed_database()`) and `state_machine` (for `run_with_config()`)
- `seed.py` is standalone
- `state_machine.py` is standalone; `run_with_config()` is the programmatic entry point
- No circular imports

**Database path resolution:**
1. `--db` CLI flag (highest priority)
2. `MATSYA_DB` environment variable
3. `matsya.db` (default)

---

## Known Gaps (Deferred)

- `profile_components.params` column is populated as `{}` — no override logic implemented
- `sm status` does not read a persisted state file from `state_machine.py` (the state machine does not yet write state as it progresses — that's a future sprint)
- `sm run` passes profile data via environment variables, which works but is not the most elegant interface for phase scripts
- Generation overwrites existing `.opencode/agents/*.md` files unconditionally (no diff/warning)
- `--db` flag must precede the subcommand (`sm --db x.db seed`, not `sm seed --db x.db`)

---

*End of Sprint 01. Six features built. One variant test passed. The spiral turns.*
