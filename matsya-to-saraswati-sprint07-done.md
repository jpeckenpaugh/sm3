# Matsya to Saraswati — Sprint 07 Complete

The bug is dead. The duplication is gone. Here is what I built.

---

## What Changed

### New file: `src/genesis_sm/generator.py` (181 lines)

Six public functions extracted from `cli.py`, each with the leading underscore removed:

| Function | Purpose |
|----------|---------|
| `deep_merge()` | Recursive dict merge for permission inheritance |
| `safe_json_loads()` | Handle double-encoded JSON from database columns |
| `resolve_inheritance_chain()` | Walk `base_profile` from child to root |
| `get_mode_flag()` | Extract mode flag from `header.role` (regex `— MODE mode`) |
| `assemble_components()` | Collect/merge components across chain, substitute `<MODE_FLAG>` and `{{ params }}` |
| `permissions_to_yaml()` | Convert permissions dict to YAML without PyYAML |

### Modified file: `src/genesis_sm/cli.py` (~147 lines removed, ~8 lines added)

1. **Import** — Added `from genesis_sm.generator import (...)`
2. **Removed** — All six private function definitions (`_deep_merge`, `_safe_json_loads`, `_resolve_inheritance_chain`, `_get_mode_flag`, `_assemble_components_for_profiles`, `_permissions_to_yaml`)
3. **Updated call sites** — `cmd_generate_agent()` and `cmd_profile_variant()` now call the public names from `generator.py`

### The critical fix: `cmd_init()` agent generation (lines 1036–1092)

**Before (buggy):** Inline loop that:
- Fetched only direct `profile_components` (no inheritance)
- Used `json.loads()` instead of `safe_json_loads()`
- Never substituted `<MODE_FLAG>`
- Called the now-deleted `_permissions_to_yaml()`

**After (correct):** Same loop body now:
- Calls `resolve_inheritance_chain()` to walk from root to child
- Merges permissions across the full chain via `deep_merge()`
- Calls `assemble_components()` which handles `<MODE_FLAG>` substitution and `{{ params }}` replacement
- Uses `safe_json_loads()` for double-encoded JSON safety
- Uses `permissions_to_yaml()` from the shared module

### New file: `sprint/07/test.sh` (test script)

Tests:
1. Generator module imports cleanly
2. `sm generate agents` output consistent (no regression)
3. `sm init` produces agent files with no raw `<MODE_FLAG>`
4. Inheritance resolution works (scribe-PLAN has base components)
5. Mode flags correctly substituted (PLAN, SPRINT_GATE, ENGINEER, DESIGN)
6. Output parity between `sm init` and `sm generate agents`

### New file: `sprint/07/test-results.md`

All 7 tests pass.

---

## The Architecture After the Fix

```
         cli.py                            generator.py
    ┌──────────────┐                  ┌────────────────────┐
    │ cmd_init()   │── import ──────► │ deep_merge()       │
    │              │                  │ safe_json_loads()  │
    │ cmd_generate_│                  │ resolve_inheritance│
    │   agent()    │                  │   _chain()         │
    │              │                  │ get_mode_flag()    │
    │ cmd_profile_ │                  │ assemble_components│
    │   variant()  │                  │ permissions_to_    │
    └──────────────┘                  │   yaml()           │
                                      └────────────────────┘
                                              │
                                     One implementation.
                                     Two callers. Zero duplication.
```

The bug cannot reappear. There is no longer a second implementation to fall out of sync.

---

*Built by Matsya, Sprint 07. The duplication dies here. The flood recedes.*
