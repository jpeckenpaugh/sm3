# Sprint 02 — Brief for the Engineer

*Additional context, design decisions, and architecture notes.*

---

## The Goal

Give the state machine a memory. By the end of this sprint:

1. Every phase execution is logged durably in SQLite (`phase_runs`)
2. Sprints are trackable entities (`sprints`) with manual/driven/hybrid modes
3. `sm init --db <path>` bootstraps a new self-contained project in one command
4. `sm log` and `sm sprint` let you read and write execution history
5. The existing Sprint 01 work is adopted into the log as a `manual` entry
6. A `default` project in the registry means CLI commands work without flags

---

## Key Design Decisions

### The state machine is a POC on the path to a worker/queue system

`state_machine.py` is a minimal proof of concept. It proves the logging loop works so the eventual message queue / background worker has a spec to implement against. Do not over-engineer it.

| Do | Don't |
|----|-------|
| Write synchronous INSERT/UPDATE to `phase_runs` at each transition | Add retry logic, heartbeats, or crash recovery for stale rows |
| Pass `db_path` through the `run_with_config()` config dict | Build a connection pool or async write queue |
| Accept that a killed process can leave a `running` row orphaned | Add a startup recovery step |
| Make it readable and correct | Make it fault-tolerant or production-ready |

The schema, CLI, and seed system are the long-lived assets. The state machine is a prototype.

### No `projects` table in SQLite

The database file *is* the project. Its filesystem path is its identity. A `projects` table inside the database would be self-referential metadata with no benefit.

Project discovery lives in two files:
- **`~/.sm/projects.json`** — global registry of known projects, written by `sm init`, read by auto-discovery
- **`.sm-config.json`** — per-project marker file in the project root, stores `db_path` and optional `target`

### "Default" project in the registry

The registry has a `"default"` field naming one project as the default. When no `--db` flag, `.sm-config.json`, or `SM_PROJECT` env var is found, `sm` falls back to the default project before trying the current directory's `matsya.db`.

Resolution order:

```
1. --db <path> flag?               → Use it
2. .sm-config.json in CWD?         → Use its db_path
3. SM_PROJECT env var?             → Look up name in ~/.sm/projects.json
4. "default" in ~/.sm/projects.json? → Use that project's db_path
5. matsya.db in current directory?  → Use it (compatibility fallback)
6. None of the above?              → Error
```

### `--target` deferred

`sm init` does not take a `--target` path in this sprint. All project artifacts (DB, backlog, sprint, agents) live under the same root. A future sprint can add `--target` to separate "where Matsya lives" from "where the code lives" — it's a backward-compatible addition.

---

## What to Build

### 1. `sprints` and `phase_runs` tables

Add to `schema.sql`. The existing schema file is authoritative — run it through `ensure_schema()` at init time.

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

CREATE TABLE IF NOT EXISTS phase_runs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id      INTEGER NOT NULL REFERENCES sprints(id),
    phase          TEXT    NOT NULL,
    iteration      INTEGER NOT NULL DEFAULT 1,
    attempt        INTEGER NOT NULL DEFAULT 1,
    status         TEXT    NOT NULL DEFAULT 'running'
                     CHECK (status IN ('running', 'passed', 'failed', 'skipped')),
    started_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    completed_at   TEXT,
    output_summary TEXT    DEFAULT '',
    error          TEXT    DEFAULT ''
);
```

### 2. State machine logging

In `state_machine.py`, `run_with_config()` gains:

```python
# Before running a phase
conn.execute("INSERT INTO phase_runs (sprint_id, phase, iteration, attempt, status) VALUES (?, ?, ?, ?, 'running')")

# After VERIFY passes
conn.execute("UPDATE phase_runs SET status='passed', completed_at=..., output_summary=? WHERE id=?")

# After VERIFY fails
conn.execute("UPDATE phase_runs SET status='failed', completed_at=..., error=? WHERE id=?")
```

The `db_path` and `sprint_id` come from the config dict. The state machine connects to the project database directly.

### 3. `sm log` command

Reads `sprints` + `phase_runs` and displays them:

```
sm log                    ← all sprints
sm log --sprint 2         ← specific sprint
sm log --sprint 2 --phases ← with phase detail
sm log --json             ← machine-readable
```

Tabular format for human, JSON for piping.

### 4. `sm sprint` subcommands

```
sm sprint start --number 2 --mode driven
sm sprint complete --number 2
sm sprint fail --number 2 --reason "..."
sm sprint note --number 1 --notes "..."
```

Each writes to the `sprints` table. `start` inserts a row with `status='active'`. `complete` sets `status='completed'` and `completed_at`. `fail` sets `status='failed'`. `note` updates `notes` (appends if non-empty).

### 5. `sm init --db <path>`

Steps:
1. Create `backlog/`, `sprint/`, `.opencode/agents/` alongside the DB file
2. Create a fresh SQLite database at `<path>`
3. Run `schema.sql` (which now includes `sprints` + `phase_runs`)
4. Seed profiles from `profiles/`, `components/`, `profile-components/`
5. Write `.sm-config.json` with `{ "db_path": "<absolute path>" }`
6. Generate agent files from seeded profiles
7. Add entry to `~/.sm/projects.json`

If the target directory already has `sprint/01/` or `backlog/` artifacts, prompt: *"This directory has existing sprint work. Seed Sprint 01 as 'manual'?"*

### 6. `~/.sm/projects.json` registry

Location: `~/.sm/projects.json` (configurable via `SM_PROJECTS_PATH` env var).

```json
{
  "default": "sm3",
  "projects": [
    {
      "name": "sm3",
      "db_path": "/root/sm/matsya.db",
      "created": "2026-07-07",
      "last_opened": "2026-07-10"
    }
  ]
}
```

Commands:
- `sm list projects` — reads and displays the registry
- `sm projects default <name>` — sets the `"default"` field
- `sm projects remove <name>` — removes an entry (does not delete the DB)

### 7. `.sm-config.json` auto-discovery

When no `--db` flag is given, `sm` walks up from the current directory looking for `.sm-config.json`. If found, reads `db_path` from it.

Implementation: start at `os.getcwd()`, check for `.sm-config.json`, if not found move to parent, repeat up to filesystem root. If not found, fall through to default project → `matsya.db` → error.

### 8. Default project integration

The DB resolution function (currently `get_db_path()`) gains the fallback chain described above. The `"default"` project from `~/.sm/projects.json` is resolved before falling back to `matsya.db`.

### 9. Adopt Sprint 01

Running `sm init --db matsya.db` from this directory:
- Detects `sprint/01/features.md`, `sprint/01/brief.md`, `sprint/01/summary.md`, `sprint/01/test-analysis.md`, `sprint/01/test_results.md`, `sprint/01/test.sh`
- Detects `backlog/ft001.md` through `ft010.md`
- Detects existing `matsya.db` with 6 profiles, 13 components, 14 assemblies
- Prompts to seed Sprint 01 as manual
- If yes: inserts `sprints(number=1, mode='manual', status='completed', notes='Sprint 01: Seed & CLI Toolchain. 7 features, 54 tests, variant test passed.')`
- Writes `.sm-config.json` pointing at `matsya.db`
- Adds entry to `~/.sm/projects.json`

---

## Files the Engineer Should Read First

| File | Why |
|------|-----|
| `concept03.md` | Full specification for this sprint |
| `concept3-feedback.md` | Cross-check analysis and design rationale |
| `schema.sql` | Existing schema — will add two new tables |
| `state_machine.py` | Will be modified to write phase logs |
| `sm.py` | Will gain new commands (init, log, sprint, list projects) |
| `seed.py` | Will be called by `sm init` |
| `sprint/01/summary.md` | What Sprint 01 delivered — needed for the adoption prompt |

---

## Deferred to Sprint 03+

- `sm status` rewrite (still reads from env vars/filesystem for now)
- Profile inheritance (`extends`)
- Variant creation workflow (`sm profile clone/edit`)
- Component params override system
- Profile export/import
- `sm init --target <path>` for separating DB location from code location

---

*Written by the Scribe. Built by the Engineer. The state machine remembers.*
