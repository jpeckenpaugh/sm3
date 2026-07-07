# Sprint 02 — Blocker Analysis

*Cross-check of the sprint plan against existing Sprint 01 code. Identifies gaps, missing details, and design contradictions that must be resolved before implementation.*

---

## Critical Gaps (Blockers)

### 1. Sprint lifecycle ownership — who creates sprint rows?

Two contradictory models exist in the specifications:

| Source | Model |
|--------|-------|
| `concept03.md` §How It's Written | "At sprint start: upsert sprints row with `status='active'`" — the **state machine** manages the sprint row |
| `sprint/02/brief.md` §4 | "`sm sprint start --number 2 --mode driven`" — the **user** manages sprint rows via CLI |

**If the user must pre-create sprints:** `sm run` needs a `--sprint` flag and must error if the sprint doesn't exist or isn't active.

**If the state machine auto-creates:** `sm run` needs no `--sprint` flag but must auto-increment the sprint number (find max + 1).

**What's missing:** A clear decision on which model to implement. This affects the interface of `sm run`, the internal logic of `run_with_config()`, and every downstream logging feature.

**Resolution needed before:** Features 2, 3, 4, 5 (everything except the schema).

---

### 2. `sm run` has no `--sprint` flag

Regardless of which ownership model is chosen, the state machine needs a `sprint_id` to write `phase_runs` rows. Currently:
- `sm run --profile scribe` has no `--sprint` argument
- The config dict constructed in `cmd_run()` has no `sprint_id` or `db_path` field
- `run_with_config(cfg)` does not read `sprint_id` or `db_path` from the config

Even if the state machine auto-creates sprints, it needs to pass the created `sprint_id` into the loop. There is no mechanism for this today.

**Affected files:**
- `sm.py` — `cmd_run()` and its argparse definition
- `state_machine.py` — `run_with_config()` signature and body

---

### 3. `db_path` not passed to `run_with_config()`

The state machine needs a database connection to log phase runs. The brief says "pass `db_path` through the `run_with_config()` config dict" but:

1. `run_with_config(cfg)` currently ignores any `db_path` key in the dict
2. `cmd_run()` opens a DB connection in its own scope, then closes it in `finally` *before* `run_with_config()` executes
3. There is no `sqlite3` import in `state_machine.py`

The state machine needs either:
- A `db_path` key in the config dict that it uses to open its own connection, or
- An open `conn` object passed directly (tighter coupling)

Either way, the mechanism doesn't exist yet.

---

### 4. Append-only vs. update contradiction in `phase_runs`

| Source | Says |
|--------|------|
| `concept03.md` §The Schema | "Append-only. Never updated in place — a retry creates a new row." |
| `sprint/02/brief.md` §State machine logging | "After VERIFY fails: update `status = 'failed'`, write `error`" |

These are contradictory. If `phase_runs` is truly append-only, each retry inserts a new row with `attempt=N`, and the last attempt's row carries the outcome. But the brief's pseudocode explicitly updates the existing row.

**Implications:**
- Append-only means stale `running` rows remain for failed attempts (requires a query-time filter: `WHERE status != 'running' OR attempt = (SELECT MAX(attempt) ...)`)
- Updates mean the table is not truly append-only but the state is always consistent

A decision is needed before implementing Feature 2.

---

## Missing Details (Need Specification)

### 5. `sm init` has no `--yes` / `--force` flag

The adoption prompt ("Seed Sprint 01 as 'manual'?") is interactive. `sm init` may be called from scripts, CI, or automation. Without a non-interactive flag, these use cases are blocked.

**Needed:** A `--yes` or `--force` flag that auto-accepts the adoption prompt.

---

### 6. `sm sprint note` append behavior unspecified

The brief says "updates `notes` (appends if non-empty)." With what delimiter?
- Appends with a newline? `\n`
- Appends with two newlines? `\n\n`
- Prepends a timestamp? `[2026-07-07] ...`

Without a convention, the implementation will guess, and the guess may not match intent.

---

### 7. Sprint adoption detection criteria

The brief lists specific files to detect:
```
sprint/01/features.md, brief.md, summary.md, test-analysis.md, test_results.md, test.sh
```

But does not specify:
- Are all required? Or is `sprint/01/` existence sufficient?
- What if only some files exist?
- What if `sprint/01/` exists but is empty?

**Needed:** A clear rule. Recommendation: check for `sprint/01/features.md` AND `sprint/01/brief.md` — these are the essential sprint artifacts. The rest are supplementary.

---

### 8. `sm init` idempotency on existing database

What happens when `sm init --db matsya.db` is run against an already-initialized database?

| Operation | Idempotent? | Notes |
|-----------|-------------|-------|
| `ensure_schema()` | ✅ Yes — `IF NOT EXISTS` | Safe |
| Profile seeding | ✅ Yes — upsert by name | Safe |
| Agent generation | ✅ Yes — overwrites | Safe |
| `.sm-config.json` write | ✅ Yes — same content | Safe |
| Registry entry add | ❌ No — appends duplicate | Must check for existing entry before adding |

**Needed:** Registry append must become an upsert (match on `name`).

---

### 9. `~/.sm/` directory creation

`sm init` writes to `~/.sm/projects.json`, but nothing creates the `~/.sm/` directory if it doesn't exist. In Sprint 01's code, there's no `os.makedirs("~/.sm")` call anywhere.

**Needed:** Add `os.makedirs(os.path.expanduser("~/.sm"), exist_ok=True)` before writing to the registry.

---

### 10. `sm log` on an empty database

What does the user see when no sprints exist?
- Silent empty output?
- "No sprints found" message?
- Table with headers and zero rows?

**Needed:** A friendly message: "No sprints recorded. Start one with `sm sprint start --number 1 --mode driven`."

---

### 11. `sm sprint start` duplicate number

The `sprints` table has `UNIQUE(number)`. If sprint 2 already exists and the user runs `sm sprint start --number 2`, SQLite raises an `IntegrityError`. The CLI must catch this and display a helpful message rather than a raw traceback.

**Needed:** Try/except around the INSERT, catch `sqlite3.IntegrityError`, print: "Sprint {N} already exists. Use a different number or complete the existing sprint first."

---

## Design Concerns

### 12. Two entry points for the project registry

The plan specifies:
- `sm list projects` — reads `~/.sm/projects.json`
- `sm projects default <name>` — writes `~/.sm/projects.json`
- `sm projects remove <name>` — writes `~/.sm/projects.json`

These are two separate command trees (`sm list` and `sm projects`) for the same data store. This means:
- Inconsistent discoverability (`sm list projects` shows up under `sm list`, not `sm projects list`)
- The user must remember two entry points
- Future registry commands (rename, show details, etc.) must be placed in one tree or the other

**Recommendation:** Unify under `sm projects`:
- `sm projects list` (replaces `sm list projects`)
- `sm projects default <name>`
- `sm projects remove <name>`

Or keep `sm list projects` as an alias for `sm projects list` for convenience.

---

### 13. Two sources of truth for runtime state (deferred)

`sm status` (Sprint 01) reads from filesystem + env vars. `sm log` (Sprint 02) reads from `sprints` + `phase_runs` tables. Until Sprint 03 rewrites `sm status`, both commands show execution state from different sources. A user checking `sm status` may see "Never run" while `sm log` shows completed sprints.

This is acknowledged as deferred in the brief, but it will cause confusion until resolved.

---

### 14. `.sm-config.json` uses absolute paths

The brief specifies absolute paths for `db_path` in `.sm-config.json`. This means:
- Moving the project directory breaks the config
- Cloning to a new location requires re-running `sm init`
- The config is not portable across environments

Relative paths would survive moves but break if the working directory doesn't match expectations. The brief chose absolute, which is a valid tradeoff — but it means `.sm-config.json` is not git-friendly for collaborative projects where different developers clone to different absolute paths.

---

## Summary

| Priority | Issue | Blocks | Recommendation |
|----------|-------|--------|----------------|
| 🔴 Critical | Sprint ownership model | Features 2–5 | Decide: user-managed (`--sprint`) or machine-managed (auto-create) |
| 🔴 Critical | No `--sprint` flag on `sm run` | Feature 2 | Add `--sprint` to `sm run` (regardless of ownership choice) |
| 🔴 Critical | No `db_path` in state machine config | Feature 2 | Add `db_path` to config dict and import sqlite3 in state_machine.py |
| 🔴 Critical | Append-only vs. update contradiction | Feature 2 | Choose: true append-only with stale rows, or allow updates |
| 🟡 Missing | `--yes` flag for `sm init` | Feature 5 | Add `--yes` / `--force` |
| 🟡 Missing | `sm sprint note` delimiter | Feature 4 | Specify: `\n\n` + timestamp prefix |
| 🟡 Missing | Adoption detection criteria | Feature 9 | Rule: detect `sprint/01/features.md` AND `sprint/01/brief.md` |
| 🟡 Missing | Registry deduplication | Feature 6 | Upsert registry entries by name |
| 🟡 Missing | `~/.sm/` directory creation | Feature 6 | Add `os.makedirs()` before registry write |
| 🟡 Missing | Empty log message | Feature 3 | Show friendly "no sprints" message |
| 🟡 Missing | Duplicate sprint error | Feature 4 | Catch `IntegrityError`, show helpful message |
| ⚪ Concern | Two registry entry points | Feature 8 | Unify under `sm projects` |
| ⚪ Concern | Dual status sources | — | Acknowledged, deferred to Sprint 03 |
| ⚪ Concern | Absolute paths in config | — | Accepted tradeoff, document in .sm-config.json |

---

*Resolve the four critical blockers before beginning implementation. The missing details can be decided inline during development. The design concerns are notes for future sprints.*

---

## Scribe's Response to Blockers

*Reviewed and resolved. The brief and concept03.md have been updated to reflect these decisions.*

---

### Critical Blocker 1 — Sprint lifecycle ownership

**Resolved.** The two models are mode-dependent, not contradictory:

| Mode | Who manages the sprint row? |
|------|---------------------------|
| `driven` | State machine auto-creates on `sm run` (max number + 1) |
| `manual` | User via `sm sprint start/complete/fail/note` |
| `hybrid` | Starts driven, user intervenes, machine updates mode to `hybrid` |

`sm run` does **not** need a `--sprint` flag. The machine auto-creates the sprint. Resume-after-crash is deferred (the POC doesn't need it).

**Updated in:** `sprint/02/brief.md` §Sprint lifecycle ownership

---

### Critical Blocker 2 — No `--sprint` flag on `sm run`

**Resolved by #1.** No flag needed. State machine creates the sprint.

---

### Critical Blocker 3 — `db_path` not passed to `run_with_config()`

**Resolved.** Two changes:

1. `cmd_run()` in `sm.py` adds `db_path` to the config dict before calling `run_with_config(cfg)`
2. `run_with_config()` imports `sqlite3` and opens its own connection using `cfg["db_path"]` — separate from the CLI's profile-loading connection

The CLI opens one connection to load the profile and assemble components, then passes `db_path` in the config dict so the state machine opens its own connection for logging. This avoids sharing cursors across scopes.

**Updated in:** `sprint/02/brief.md` §2. State machine logging

---

### Critical Blocker 4 — Append-only vs. update contradiction

**Resolved.** The `phase_runs` row for the current attempt **is updated** on completion. "Append-only" means rows are never deleted — not that every operation is an INSERT.

| Event | Action |
|-------|--------|
| Phase starts | INSERT with `status='running'` |
| Phase passes | UPDATE same row: `status='passed'`, `completed_at`, `output_summary` |
| Phase fails | UPDATE same row: `status='failed'`, `completed_at`, `error` |
| Retry | New INSERT with `attempt = attempt + 1` |

This gives an auditable history (each attempt is its own row) while keeping state cleanly queryable.

**Updated in:** `concept03.md` §The Schema (line 63), `sprint/02/brief.md` §phase_runs update model

---

### Missing Detail 5 — `--yes` flag for `sm init`

**Resolved.** Added `--yes` flag. When set, auto-accepts the adoption prompt without waiting for user input. Default remains interactive.

**Updated in:** `sprint/02/brief.md` §5. `sm init --db <path>`

---

### Missing Detail 6 — `sm sprint note` delimiter

**Resolved.** Convention: prepend `[YYYY-MM-DD]` timestamp, append with `\n\n` separator.

Example — running `sm sprint note --number 1 --notes "Adjusted scope"` appends:
```
\n\n[2026-07-07] Adjusted scope
```

**Updated in:** `sprint/02/brief.md` §4. `sm sprint` subcommands

---

### Missing Detail 7 — Adoption detection criteria

**Resolved.** Check for **both** `sprint/01/features.md` AND `sprint/01/brief.md`. Both must exist to trigger the "Seed Sprint 01 as manual?" prompt. If only one exists, skip the prompt (the directory is partially populated).

**Updated in:** `sprint/02/brief.md` §5. `sm init --db <path>` (adoption detection)

---

### Missing Detail 8 — Registry deduplication

**Resolved.** Upsert registry entries by `name`. If an entry with the same name already exists in `~/.sm/projects.json`, update its `last_opened` field instead of appending a duplicate.

**Updated in:** `sprint/02/brief.md` §5. `sm init --db <path>` (step 8)

---

### Missing Detail 9 — `~/.sm/` directory creation

**Resolved.** Add `os.makedirs(os.path.expanduser("~/.sm"), exist_ok=True)` as the first step of `sm init`, before any registry write.

**Updated in:** `sprint/02/brief.md` §5. `sm init --db <path>` (step 1)

---

### Missing Detail 10 — Empty log message

**Resolved.** `sm log` on an empty database prints: "No sprints recorded. Start one with `sm sprint start --number 1 --mode driven`." With `--json`, outputs `[]`.

**Updated in:** `sprint/02/brief.md` §3. `sm log` command

---

### Missing Detail 11 — Duplicate sprint error

**Resolved.** Catch `sqlite3.IntegrityError` on `sm sprint start --number N` when sprint N already exists. Display: "Sprint {N} already exists. Use a different number or complete the existing sprint first."

**Updated in:** `sprint/02/brief.md` §4. `sm sprint` subcommands

---

### Design Concern 12 — Two registry entry points

**Not changed.** `sm list projects` is a read-only display command living alongside `sm list profiles` and `sm list components`. `sm projects default` and `sm projects remove` are mutation commands. This split follows the pattern already established in Sprint 01 (`sm list` for reads, `sm generate` and `sm seed` for writes). The two trees serve different purposes and are equally discoverable via `--help`.

---

### Design Concern 13 — Dual status sources

**Acknowledged, deferred to Sprint 03.** The brief already lists the `sm status` rewrite as deferred. A note has been added to the deferred section.

---

### Design Concern 14 — Absolute paths in config

**Accepted tradeoff.** Relative paths would require the runtime to know the config file's location, adding complexity with no current benefit. The project directory is not expected to move during its lifetime.

---

### Files updated with these resolutions

| File | Changes |
|------|---------|
| `concept03.md` | Line 63: relaxed strict "append-only" language to match the update model |
| `sprint/02/brief.md` | Added sprint ownership model, `phase_runs` update model, `db_path`/`sqlite3` details, `--yes` flag, adoption criteria, note delimiter, empty log message, duplicate sprint error, registry dedup, `~/.sm/` dir creation |
| This file | This response appended below |

---
