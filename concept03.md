# Concept 03 — Durable Execution Log

*A Warden's directive for the Scribe and Builder.*  
*Give the state machine a memory.*

---

## The Problem

The state machine runs but forgets everything. Iteration count resets on restart. There is no record of what happened in a previous sprint, which phases failed, or why. `sm status` infers state from the filesystem and environment variables rather than reading from a durable log.

Meanwhile, sprints can happen outside the state machine — manual work, ad-hoc experiments, the Origin making changes by hand. The system needs a single honest record of all sprints, regardless of how they were executed.

---

## The Schema

Two new tables in the existing SQLite database:

### sprints

One row per sprint. Records the sprint regardless of how it was run.

```sql
CREATE TABLE IF NOT EXISTS sprints (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    number       INTEGER NOT NULL,
    mode         TEXT    NOT NULL DEFAULT 'driven'
                         CHECK (mode IN ('driven', 'manual', 'hybrid')),
    status       TEXT    NOT NULL DEFAULT 'planned'
                         CHECK (status IN ('planned', 'active', 'completed', 'failed', 'aborted')),
    started_at   TEXT,
    completed_at TEXT,
    notes        TEXT    DEFAULT '',
    UNIQUE(number)
);
```

- `mode` — how the sprint was executed. `driven` = by the state machine. `manual` = by hand. `hybrid` = mixed.
- `status` — lifecycle state. `aborted` is distinct from `failed`: failed means it exhausted retries, aborted means a human stopped it intentionally.
- `notes` — free text for context: why a mode changed, what went wrong, what was learned.

### phase_runs

One row per phase execution within a sprint. Append-only log of every attempt.

```sql
CREATE TABLE IF NOT EXISTS phase_runs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id    INTEGER NOT NULL REFERENCES sprints(id),
    phase        TEXT    NOT NULL,
    iteration    INTEGER NOT NULL DEFAULT 1,
    attempt      INTEGER NOT NULL DEFAULT 1,
    status       TEXT    NOT NULL DEFAULT 'running'
                         CHECK (status IN ('running', 'passed', 'failed', 'skipped')),
    started_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    completed_at TEXT,
    output_summary TEXT DEFAULT '',
    error        TEXT DEFAULT ''
);
```

- Append-only. Never updated in place — a retry creates a new row.
- `output_summary` — brief description of what the phase produced. The state machine writes this after VERIFY.
- `error` — error message if failed, empty if passed.

---

## Projects — Sealed Microverses

The state machine does not operate on itself. It is pointed at a **project** — a directory containing its own SQLite database, working directories, and generated agent files. Each project is a self-contained microverse with no global fallback.

### The Principle

> Every artifact a project needs lives inside the project. There is no "shared global profile." If it's not in the project's database, it doesn't exist for that project.

### projects table

```sql
CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    root_path   TEXT    NOT NULL UNIQUE,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    active      INTEGER NOT NULL DEFAULT 1
);
```

One row per project. The database is local to the project directory. The canonical profiles database (seed JSON) is a separate artifact used only at init time.

### `sm init <path>` — Project Bootstrap

Creates a new project at the given path:

1. Create directory structure: `backlog/`, `sprint/`, `.opencode/agents/`
2. Create a fresh SQLite database at `<path>/project.db`
3. Create `sprints`, `phase_runs`, and `projects` tables
4. Seed the six canonical profiles into `<path>/project.db` from seed JSON
5. Write a `.sm-config.json` marker file identifying this as a managed project
6. Generate initial agent files from the seeded profiles via `sm generate agent`

After init, the project is fully self-contained. The database at `project.db` is the single source of truth for that project's profiles, sprints, and execution history.

### `sm --project <path>` — Targeting a Project

All commands accept a `--project` flag pointing to the project directory:

```bash
sm --project ~/workspaces/my-app init                 # (--project is implicit here)
sm --project ~/workspaces/my-app status
sm --project ~/workspaces/my-app run --profile scribe
sm --project ~/workspaces/my-app list profiles
sm --project ~/workspaces/my-app log --sprint 2
```

The state machine reads `project.db` from the target project. It never falls back to a global profile or a different database.

### `sm init` from an existing directory

If the target path already has a project structure (backlog/, sprint/, etc.), `sm init` detects the existing artifacts and asks:

- "This directory appears to have active sprint work. Seed a manual sprint entry to acknowledge it?"
- If yes, it creates a Sprint 01 entry with `mode: manual` and populates the log.

This is how we seed the current working directory as a project without losing the work already done.

### No Global Fallback

The state machine has one rule for profile resolution:

1. Check `project.db` → `profiles` table
2. If not found → error: "Profile 'x' not found in this project. Use `sm init --seed` or add it manually."

No fallback to a global profiles database. No assumption that a profile exists because it exists in another project. Each project is its own world.

---

## How It's Written

### State machine (driven mode)

At each phase transition, the state machine appends to `phase_runs`:

1. Before running a phase: insert a row with `status = 'running'`
2. After VERIFY passes: update `status = 'passed'`, write `output_summary`
3. After VERIFY fails: update `status = 'failed'`, write `error`
4. At sprint start: upsert `sprints` row with `status = 'active'`
5. At sprint end: set `sprints.status = 'completed'`

The state machine loop gains a new dependency: a database connection for logging. This is in addition to its existing config-driven execution.

### Manual mode

The `sm sprint` subcommands provide a way to seed the log without running the state machine:

```
sm sprint start --number 1 --mode manual
sm sprint complete --number 1
sm sprint fail --number 1 --reason "Spec changed mid-sprint"
sm sprint note --number 1 --notes "Sprint 1 was manual. 7 features, 54 tests, variant test passed."
```

These commands let the Origin record work done outside the machine.

### Hybrid mode

A sprint starts as `driven`. The machine fails a phase. The Origin intervenes, fixes the issue by hand, and resumes. The sprint mode is updated to `hybrid`. A note explains the transition.

---

## How It's Read

### `sm status`

Displays a merged view from both the execution log and the filesystem:

```
Project: ~/workspaces/my-app
──────────────────────────────
Database:  project.db (6 profiles, 13 components, 14 assemblies)
Sprint 1  (manual, completed, 7 features, 54 tests)
Sprint 2  (driven, active, iteration 4/10, phase: ENGINEER)
Backlog:  3 feature files
Signal:   absent
```

If the execution log is empty (fresh database, never run), status shows:

```
Sprint 1  (manual, completed, 7 features, 54 tests)  ← seeded by user
```

If the log has never been seeded and the filesystem has no sprint artifacts:

```
State:   Never run — seed and run to begin
```

### `sm log`

A new command for viewing the raw execution history:

```
sm log [--sprint <number>] [--phases] [--json]
```

Example output:

```
Sprint 1 (manual) ─────────────────────────────────────
  No phase log (manual sprint)

Sprint 2 (driven, active) ─────────────────────────────
  PLAN      iter 1  attempt 1  passed     "Planning complete"
  WRITE     iter 1  attempt 1  passed     "Artifacts written"
  REVIEW    iter 1  attempt 1  failed     "File not found"
  REVIEW    iter 1  attempt 2  passed     "File confirmed"
  COMMIT    iter 1  attempt 1  passed     "Commit marker created"
  GATE      iter 1  attempt 1  passed     "Backlog non-empty, continuing"
```

---

## What This Enables

- **Resume after crash** — the state machine reads the last `phase_runs` entry and picks up where it left off
- **Post-sprint analysis** — "Sprint 2 had 4 phase failures, all in ENGINEER, all syntax errors"
- **Honest accounting** — manual, driven, and hybrid sprints coexist in one log
- **Trend tracking** — failure rates, phase durations, retry counts over multiple sprints

---

## Open Questions for the Builder

1. Should `phase_runs` be written synchronously (blocking the state machine) or asynchronously (fire-and-forget)? Synchronous is safer; async could lose entries on crash.
2. Should the state machine's config.json include a `db_path` field for the execution log, or should it always use the same database as profiles?
3. How does `sm status` handle the gap between the log and the filesystem? Display both and let the human reconcile? Auto-seed from git history?
4. Should there be an `sm log prune` command for archiving old phase runs, or is append-only forever the right model?
5. **Project discovery** — should `sm status` without `--project` scan the current directory for a `.sm-config.json` marker, or require the flag always?
6. **Profile mutation** — if a user edits a profile within a project (via `sm profile edit`), should `sm generate agent` reflect those changes immediately, or should there be a `sm sync` step?

---

## What This Sprint Delivers

1. The `projects` table in `schema.sql`
2. `sm init <path>` — bootstraps a new project with its own database, seeded profiles, and directory structure
3. `--project <path>` flag on all commands for targeting a specific project
4. Two new tables (`sprints`, `phase_runs`) for execution history
5. `seed.py` updated to create all new tables during init
6. State machine writes to `phase_runs` during execution
7. `sm sprint start/complete/fail/note` subcommands for manual logging
8. `sm status` reads from execution log instead of inferring from env vars
9. `sm log` command for viewing execution history
10. Seeding Sprint 01 as a manual sprint so the log matches reality
11. No global profile fallback — each project is its own sealed world

---

*Written by the Warden. The state machine remembers. The spiral turns.*
