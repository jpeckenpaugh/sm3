# Concept 03 — Cross-Check Analysis

*Reviewed by the Scribe against intent, practicality, and best practice.*

---

## What Concept 03 Proposes

| Component | Purpose |
|-----------|---------|
| `sprints` table | One row per sprint, tracks mode (driven/manual/hybrid) and status |
| `phase_runs` table | Append-only log of every phase attempt |
| `projects` table | Registry of sealed project directories |
| `sm init <path>` | Bootstrap a new project with its own DB, profiles, and structure |
| `--project <path>` | Target all commands at a specific project |
| `sm sprint` | Subcommands for manual logging |
| `sm log` | View execution history |
| **No global fallback** | Each project is sealed — no shared profiles |

---

## Intent Check

**Problem identified in Concept 03:** The state machine forgets everything. No record of past sprints, no resume after crash, no tracking of manual work.

**Does this problem exist?** Yes. We flagged these exact gaps in our Sprint 01 analysis:

| Gap we flagged | Concept 03 addresses it? |
|----------------|-------------------------|
| State machine forgets everything (ft005 known gap) | ✓ `phase_runs` log |
| `sm status` infers from filesystem/env vars | ✓ Reads from execution log |
| No record of manual work | ✓ `mode = 'manual'` sprints |
| No resume after crash | ✓ Reads last `phase_runs` entry |
| `profile_components.params` column unused | ✗ (not addressed — separate concern) |

**Verdict:** The intent is sound and addresses real gaps we already identified.

---

## Practicality Check: Conflicts with Sprint 01

### Conflict 1 — `--db` vs `--project`

Our current system uses `--db test.db` to point to a database file. Concept 03 replaces this with `--project ~/workspace` which resolves to `~/workspace/project.db`.

```
Current:   sm --db matsya.db seed
            sm --db matsya.db run --profile scribe

Concept 3: sm --project ~/workspace init
            sm --project ~/workspace run --profile scribe
```

These flag models are incompatible. Resolution options:
- Deprecate `--db` in favor of `--project`
- Keep both, with `--project` taking precedence
- Auto-detect project from `.sm-config.json` when neither flag is given

### Conflict 2 — State machine needs a DB connection

The current `state_machine.py` is a pure loop — it reads a config dict, runs bash scripts, checks files. It has zero SQLite awareness. Concept 03 wants it to write to `phase_runs` synchronously at every phase transition:

```python
conn = sqlite3.connect(project_db)
conn.execute("INSERT INTO phase_runs ...")
```

This is a new coupling between the state machine and the database. Not wrong, but a significant architectural change to a file that otherwise had no SQLite dependency.

**Risk:** A script failure could leave a `phase_runs` row stuck at `status='running'`. The concept acknowledges sync is safer than async, but robust error handling is essential.

### Conflict 3 — `sm status` rewrite

Our ft005 implementation reads from filesystem + environment variables. Concept 03 wants it to read from `sprints` + `phase_runs` tables. This is a near-complete rewrite — not an addition.

### Conflict 4 — `seed.py` scope creep

`seed.py` currently seeds profiles/components/profile-components. Concept 03's `sm init` would:
- Create directory structure (backlog/, sprint/, .opencode/agents/)
- Create a fresh database
- Run the schema (with 3 new tables)
- Seed profiles (reusing existing seed JSON)
- Generate agent files
- Write `.sm-config.json`

This is a new command (`init`) that wraps seeding rather than extending `seed.py`.

### What survives intact

- The profile/component/assembly system from Sprint 01 ✓
- The `roles_example_opt.md` decomposition design ✓
- The seed JSON files in `profiles/`, `components/`, `profile-components/` ✓
- `sm generate agent` — just needs a `--project` flag ✓
- The variant test — works the same way in a project context ✓

---

## Best Practice Check

### Strengths

| Practice | Assessment |
|----------|-----------|
| Append-only log | Durable, auditable, no data loss |
| Sealed projects | Strong isolation, no cross-project contamination |
| CHECK constraints | Enum validation at the DB level — good SQLite practice |
| `driven` / `manual` / `hybrid` | Honest about how work actually happens in practice |
| `failed` vs `aborted` | Important semantic distinction often overlooked |

### Concerns

| Practice | Concern |
|----------|---------|
| `projects` table | Self-referential metadata — the database file *is* the project. A `projects` table recording itself feels redundant. The `.sm-config.json` marker file already identifies a project directory. Consider whether this table earns its keep. |
| Synchronous DB writes | The state machine runs bash scripts via subprocess. If the script crashes mid-phase, the `phase_runs` row is stuck at `status='running'`. Needs a timeout or heartbeat mechanism, or a startup check that cleans stale `running` entries. |
| Scope size | ~10 deliverables: 3 new tables, `init` command, `--project` flag, `sprint` subcommands, `log` command, `status` rewrite, state machine logging, no-fallback enforcement, migration path. This is 2–3 sprints of work, not one. |
| Duplicated profiles | Each project copies the 6 canonical profiles into its own DB. If a profile definition changes upstream, existing projects keep their version. Consistent with "no global fallback," but profile updates become a manual propagation problem. |

---

## The Migration Question

The current working directory **is** effectively a Sprint 01 project already — it has:
- A seeded database with profiles, components, and assemblies
- A backlog with 10 feature files (6 active + 4 deferred)
- Sprint 01 artifacts (features.md, brief.md, summary.md, test-analysis.md, test_results.md, test.sh)
- Generated test results showing 54 passed tests

Concept 03 acknowledges this with "seed from existing directory" but doesn't specify a concrete migration path. Key questions:
- Does `sm init .` detect the existing `matsya.db` and adopt it as `project.db`?
- Does it create a Sprint 01 `manual` entry from the existing artifacts?
- How does it reconcile the filesystem state (backlog files, sprint directory) with the DB state?

---

## Summary

| Dimension | Rating |
|-----------|--------|
| **Intent** | ✓ Solves real, identified gaps |
| **Alignment** | ✓ Builds correctly on Sprint 01's profile/component system |
| **Practicality** | ⚠ Conflicts with `--db` flag; requires state machine refactor; `projects` table may be unnecessary |
| **Scope** | ⚠ ~10 deliverables — likely 2–3 sprints, not 1 |
| **Migration** | ❓ Current Sprint 01 artifacts need a concrete migration path |

---

*Written by the Scribe. Reviewed against what is built, what is needed, and what is wise.*
