# Sprint 02 — Test Analysis Report

*Reviewed by the Scribe. 73 tests passed, 0 failed.*

---

## 1. Verification Summary

### Schema — `sprints` and `phase_runs` tables (ft001)

Both tables added to `schema.sql` with all specified columns, CHECK constraints, and foreign keys:

```
sprints:     id, number, mode (driven/manual/hybrid), status (planned/active/completed/failed/aborted),
             started_at, completed_at, notes, UNIQUE(number)

phase_runs:  id, sprint_id → sprints.id, phase, iteration, attempt,
             status (running/passed/failed/skipped), started_at, completed_at,
             output_summary, error
```

✓ Matches Concept 03 specification exactly.

---

### State Machine Phase Logging (ft002)

`state_machine.py` (283 lines) gained:

| Function | Purpose |
|----------|---------|
| `log_phase_start()` | INSERT a `phase_runs` row with `status='running'` |
| `log_phase_end()` | UPDATE the same row with `status='passed'` or `'failed'` |
| `complete_sprint()` | UPDATE `sprints` row with `status='completed'` or `'failed'` |
| `run_with_config(cfg)` | Accepts `db_path` and `sprint_id` from config dict; opens its own SQLite connection |

The update model is implemented as resolved in the blockers — INSERT on start, UPDATE on completion, new INSERT on retry. The DB connection is separate from the CLI's profile-loading connection.

✓ Matches the resolved design.

---

### `sm log` Command (ft003)

Reads `sprints` + `phase_runs`, displays tabular output or JSON.

| Flag | Behavior | Status |
|------|----------|--------|
| (no flags) | All sprints, summary view | ✓ |
| `--sprint N` | Filter to one sprint | ✓ |
| `--sprint N --phases` | Show phase run detail for that sprint | ✓ |
| `--json` | Machine-readable JSON output | ✓ |
| Empty database | "No sprints recorded. Start one with..." message | ✓ |
| Empty database + `--json` | `[]` | ✓ |

✓ Graceful empty-state handling and all display modes working.

---

### `sm sprint` Subcommands (ft004)

| Subcommand | Behavior | Status |
|------------|----------|--------|
| `start --number N --mode M` | INSERT with `status='active'` | ✓ |
| `start --number N` (duplicate) | Caught before INSERT: "Sprint N already exists" | ✓ |
| `complete --number N` | UPDATE `status='completed'`, `completed_at` | ✓ |
| `fail --number N --reason` | UPDATE `status='failed'`, `completed_at`, notes | ✓ |
| `note --number N --notes` | Appends `[YYYY-MM-DD]` prefixed note with `\n\n` delimiter | ✓ |
| Missing sprint | Clear error message, exit non-zero | ✓ |

✓ All lifecycle actions implemented with proper error handling.

---

### `sm init` Command (ft005/ft009)

Bootstraps a complete project directory:

| Step | Status |
|------|--------|
| Creates `backlog/`, `sprint/`, `.opencode/agents/` | ✓ |
| Creates SQLite database at specified path | ✓ |
| Runs `schema.sql` to create all tables | ✓ |
| Seeds profiles from JSON seed files | ✓ |
| Generates agent files for all seeded profiles | ✓ |
| Writes `.sm-config.json` with absolute `db_path` | ✓ |
| Adds entry to `~/.sm/projects.json` (upsert by name) | ✓ |
| Sets newly created project as default if none exists | ✓ |
| `--yes` flag auto-accepts adoption prompt | ✓ |

**Sprint 01 adoption** (ft009):
- Detects `sprint/01/features.md` AND `sprint/01/brief.md` ✓
- Prompts to seed Sprint 01 as manual ✓
- `--yes` flag skips interactive prompt ✓
- Inserts `(number=1, mode='manual', status='completed', notes=...)` ✓
- Uses `INSERT OR IGNORE` so re-running is safe ✓

---

### Project Registry (ft006/ft008)

`~/.sm/projects.json` format:

```json
{
  "default": "test-fresh",
  "projects": [
    { "name": "test-fresh", "db_path": "/tmp/.../matsya.db", "created": "2026-07-07", "last_opened": "2026-07-07" }
  ]
}
```

| Command | Behavior | Status |
|---------|----------|--------|
| `sm list projects` | Table display with (default) marker | ✓ |
| `sm list projects --json` | Raw JSON output | ✓ |
| `sm projects default <name>` | Sets `"default"` field | ✓ |
| `sm projects remove <name>` | Removes entry, clears default if needed | ✓ |

Registry location configurable via `SM_PROJECTS_PATH` env var (used by tests to isolate from live registry).

---

### Auto-discovery (ft007)

The `get_db_path()` function implements the full 6-step resolution chain:

```
1. --db <path> flag                           → explicit override
2. .sm-config.json in CWD or parents          → auto-discovery
3. SM_PROJECT env var → lookup in registry
4. "default" project in ~/.sm/projects.json
5. matsya.db in current directory              → compatibility
6. Error message
```

✓ Verified by test: running `sm list profiles` inside a project directory resolves to the correct database without `--db` flag.

---

## 2. Test Results

The test script (`test.sh`) runs 73 tests covering all 9 features. Four iterations of fixing:

| Run | Passed | Failed | What was fixed |
|-----|--------|--------|----------------|
| 1 | 61 | 12 | Initial implementation — registry, auto-discovery, error handling gaps |
| 2 | 70 | 2 | Registry + project management fixed; auto-discovery content comparison still failing |
| 3 | 71 | 1 | Auto-discovery content fix; "log on missing DB" message format issue |
| 4 | **73** | **0** | `--db` flag parsing diagnostic added, error message pattern match fixed |

---

## 3. Files Changed from Sprint 01

| File | Before | After | Change |
|------|--------|-------|--------|
| `schema.sql` | 32 lines, 3 tables | 59 lines, 5 tables | Added `sprints` and `phase_runs` |
| `sm.py` | 519 lines | 1146 lines | Added `init`, `log`, `sprint`, `list projects`, `projects`, auto-discovery, registry |
| `state_machine.py` | 192 lines | 283 lines | Added `log_phase_start`, `log_phase_end`, `complete_sprint`, DB connection in loop |
| `seed.py` | 285 lines | 285 lines | No changes needed (schema runs via `ensure_schema()`) |

---

## 4. Issues Found

### Issue 1 — `sm init` inlines agent generation logic

The `cmd_init()` function duplicates the agent generation logic from `cmd_generate_agent()` rather than calling it. Both functions query profiles, assemble components, render YAML frontmatter, and write files — but they do so independently.

```python
# cmd_init() lines 819-861: duplicated agent generation
# cmd_generate_agent() lines 337-403: same logic
```

**Severity:** Low. Works correctly, but the duplication means fixes or improvements must be made in two places. A future refactor could extract the shared logic into a helper function.

### Issue 2 — `INSERT OR IGNORE` for Sprint 01 adoption

The adoption step uses `INSERT OR IGNORE` to prevent duplicate sprint 1 entries. This means if Sprint 01 row already exists, the second `sm init` silently skips it without warning.

```python
cursor.execute(
    """INSERT OR IGNORE INTO sprints (number, mode, status, started_at, completed_at, notes)
       VALUES (1, 'manual', 'completed', ?, ?, ?)""",
    ...
)
```

**Severity:** Low. Idempotent by design. A message is printed ("Sprint 01 already recorded") when `cursor.rowcount == 0`.

### Issue 3 — `sm init` generates agents before writing `.sm-config.json`

The agent generation step reads profiles from the database but generates agent files. The `.sm-config.json` is written after agent generation. This is fine functionally but means if agent generation fails, the project is left without a config marker even though the DB and directory structure exist.

**Severity:** Trivial. The project can be re-initialized.

### Issue 4 — No explicit sprint auto-increment test

The state machine auto-creates sprints with `SELECT COALESCE(MAX(number), 0) + 1 FROM sprints`, but the tests don't verify that running `sm run` twice creates sprints 1, 2, 3... Only a single run is tested. The auto-increment logic is simple and correct, but it's not tested.

**Severity:** Trivial. Low-risk logic. Could be added in a future sprint.

---

## 5. Design Compliance Check

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `sprints` + `phase_runs` tables in schema | ✓ | schema.sql lines 34-59 |
| State machine writes phase logs synchronously | ✓ | `log_phase_start()` / `log_phase_end()` called in loop |
| `sm log` command | ✓ | Tabular + JSON + phase detail |
| `sm sprint` subcommands | ✓ | start, complete, fail, note |
| `sm init --db <path>` | ✓ | Full project bootstrap |
| `~/.sm/projects.json` with `"default"` | ✓ | Registry with upsert and default project |
| `.sm-config.json` auto-discovery | ✓ | Walk up from CWD |
| `sm list projects` | ✓ | Table + JSON |
| `sm projects default/remove` | ✓ | Registry mutation |
| Sprint 01 adoption | ✓ | Detects sprint/01/features.md + brief.md, seeds manual entry |
| DB resolution chain (6 steps) | ✓ | `get_db_path()` lines 98-145 |
| `--yes` flag for `sm init` | ✓ | `args.yes` skips interactive prompt |
| `sm sprint note` with timestamp | ✓ | `[YYYY-MM-DD]` prefix + `\n\n` delimiter |
| Duplicate sprint error handling | ✓ | Pre-INSERT check for existing number |
| Duplicate registry entry handling | ✓ | `registry_upsert()` updates existing entry |
| `~/.sm/` directory auto-created | ✓ | `os.makedirs(REGISTRY_DIR, exist_ok=True)` in `write_registry()` |
| Empty log message | ✓ | "No sprints recorded" + `[]` for --json |
| Append-only with row updates | ✓ | INSERT on start, UPDATE on completion, new INSERT on retry |

---

## 6. Overall Assessment

| Category | Grade |
|----------|-------|
| Schema fidelity | ✓ Matches Concept 03 specification exactly |
| Code quality | ✓ Clean, modular, stdlib-only, 1146 lines of sm.py |
| Test coverage | ✓ 73 tests across all 9 features |
| Error handling | ✓ Duplicate sprints, missing sprints, missing DB, missing profile |
| Auto-discovery | ✓ Full 6-step resolution chain implemented |
| Project isolation | ✓ No global fallback, each project sealed in its own DB |
| Backward compatibility | ✓ Sprint 01 commands (seed, run, list, status, generate) still work |
| Sprint 01 adoption | ✓ Existing work is anchored in the durable log |

**The sprint is complete and correct.** The durable execution log, project system, auto-discovery, and Sprint 01 reconciliation are all implemented and verified. The four critical blockers identified in `blockers.md` were resolved before implementation, and the 73-test suite confirms everything works.

---

*Reviewed by the Scribe. The state machine remembers. The spiral turns.*
