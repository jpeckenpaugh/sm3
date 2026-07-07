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

- Append-only at the sprint level — history is never lost; rows are never deleted.
- Each attempt gets its own row (incrementing `attempt`). That row's `status`, `completed_at`, `output_summary`, and `error` are **updated in place** when the attempt completes.
- A retry creates a new row with `attempt+1`; the previous attempt's row retains its final state.
- `output_summary` — brief description of what the phase produced. The state machine writes this after VERIFY.
- `error` — error message if failed, empty if passed.

---

## Projects — Sealed Microverses

The state machine is pointed at a **project** — a directory containing its own SQLite database (`project.db`), working directories, and generated agent files. Each project is a self-contained microverse with no global fallback.

### The Principle

> Every artifact a project needs lives inside the project. The database file *is* the project — not a record within it.

There is no `projects` table inside the database. The database file itself is the project identity. Its path in the filesystem is its name.

### The Registry (`~/.sm/projects.json`)

A flat JSON file maintained by the CLI for project discovery:

```json
{
  "default": "sm3",
  "projects": [
    {
      "name": "sm3",
      "db_path": "/root/sm/matsya.db",
      "created": "2026-07-07",
      "target": "agent-framework",
      "last_opened": "2026-07-10"
    }
  ]
}
```

- `"default"` — names the project used when no `--db` flag, `.sm-config.json`, or `SM_PROJECT` env var resolves
- Written by `sm init --db <path>`
- `"default"` set with `sm projects default <name>`
- Read by `sm list projects` and auto-discovery
- Human-editable in a pinch — git-friendly, grep-friendly, `jq`-friendly
- No secondary SQLite layer — JSON is the registry, directly

### `sm init --db <path>` — Project Bootstrap

Creates a new project at the given database path:

1. Create directory structure: `backlog/`, `sprint/`, `.opencode/agents/`
2. Create a fresh SQLite database at `<path>` (e.g. `matsya.db`)
3. Create `sprints` and `phase_runs` tables
4. Seed the six canonical profiles from seed JSON
5. Write a `.sm-config.json` marker file identifying this as a managed project
6. Generate initial agent files from the seeded profiles via `sm generate agent`
7. Add an entry to `~/.sm/projects.json`

After init, the project is fully self-contained. The database is the single source of truth for that project's profiles, sprints, and execution history.

### Project Discovery

When no `--db` flag is given, `sm` resolves the database in this order:

1. **`.sm-config.json`** — walk up from the current directory. If found, use its `db_path`.
2. **`SM_PROJECT` env var** — lookup the project name in `~/.sm/projects.json`. If found, use its `db_path`.
3. **`"default"` in registry** — if `~/.sm/projects.json` has a `"default"` field, use that project's `db_path`.
4. **`matsya.db` in current directory** — compatibility fallback for directories not yet initialized as projects.
5. **None of the above** — error: "No project found. Run `sm init --db <path>` or specify `--db`."

The user can always override any step with explicit `--db <path>`.

### Adopting the Current Directory

The current working directory already has a seeded database (`matsya.db`), a sprint structure, and a backlog. Running `sm init --db matsya.db` from this directory:

1. Detects existing `sprint/01/` with artifacts
2. Detects existing `backlog/` with feature files
3. Detects existing `matsya.db` with profiles
4. Prompts: "This directory has existing sprint work. Seed Sprint 01 as 'manual'?"
5. If yes, inserts a `sprints` row: `(number=1, mode='manual', status='completed', notes='Sprint 01 built by hand. 7 features, 54 tests, variant test passed.')`
6. Writes `.sm-config.json` pointing at the existing `matsya.db`
7. Adds entry to `~/.sm/projects.json`

Nothing is overwritten. The existing work is acknowledged and anchored in the log.

### No Global Fallback

The state machine has one rule for profile resolution:

1. Check the project's database → `profiles` table
2. If not found → error: "Profile '<name>' not found in this project. Run `sm init --seed <path>` or add it manually."

No fallback to a global profiles database. No assumption that a profile exists because it exists in another project.

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
2. Should the state machine's config.json include a `db_path` field, or should it always connect to the project database directly?
3. How should `sm log` format output — tabular, JSON, or both?
4. Should there be an `sm log prune` command for archiving old phase runs, or is append-only forever the right model?
5. **Registry location** — `~/.sm/projects.json` is the default. Should it be configurable via an environment variable?

---

## What This Sprint Delivers

### Core (must have)

1. `sprints` table — one row per sprint, tracks mode (driven/manual/hybrid) and status
2. `phase_runs` table — append-only log of every phase attempt within a sprint
3. State machine writes to `phase_runs` during execution (synchronous, project DB connection)
4. `sm log` command — reads and displays execution history
5. `sm sprint start/complete/fail/note` subcommands — manual logging for work done outside the machine

### Project system

6. `sm init --db <path>` — bootstraps a new project: creates DB with schema, seeds profiles, writes `.sm-config.json`, generates agent files
7. `~/.sm/projects.json` — registry written by `sm init`, read by discovery; includes `"default"` field
8. `.sm-config.json` auto-discovery — when no `--db` flag is given, walk up from current directory
9. `sm list projects` — reads the registry and displays known projects
10. `sm projects default <name>` — sets the `"default"` field in the registry

### Reconciliation

11. Seed Sprint 01 as `manual` — adopt the current working directory's existing work into the log

### Explicitly deferred to Sprint 03+

- Full `sm status` rewrite (still reads from env vars/filesystem for now)
- Profile inheritance (`extends`)
- Variant creation workflow (`sm profile clone/edit`)
- Component params override system
- Profile export/import

---

## Sprint 02 Summary

| Dimension | Scope |
|-----------|-------|
| **New tables** | 2 (`sprints`, `phase_runs`) |
| **New files** | `~/.sm/projects.json` (registry), `.sm-config.json` (project marker) |
| **New commands** | `sm init`, `sm log`, `sm sprint`, `sm list projects`, `sm projects default` |
| **Modified commands** | State machine loop (writes to DB), `sm seed` (adds new tables) |
| **Deferred** | `sm status` rewrite, profile inheritance, variant workflow, params, export/import |
| **Reconciliation** | Seed existing Sprint 01 as manual entry |

---

*Written by the Warden. The state machine remembers. The spiral turns.*
