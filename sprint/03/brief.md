# Sprint 03 — Brief for the Engineer

*Additional context, design decisions, and architecture notes.*

---

## The Goal

Give the state machine a spine that can be redesigned without rewriting the engine. By the end of this sprint:

1. The phase sequence lives in the database as data (`pipeline_states` + `pipeline_transitions`), not as a hardcoded list in Python
2. Each phase declares its expected inputs and outputs, and the engine verifies them (`file_contracts`)
3. Phase scripts have a third exit channel — escalation — to signal blockage without crashing
4. The engine can fork into parallel branches when the work divides
5. Every step within a phase attempt is recorded at high resolution (`phase_events`)
6. Sprint 02 is adopted into the log as a `manual` entry, so the sprint history is continuous

---

## Key Design Decisions (made by the Scribe, refined by the Fish, reflected by the Shell)

### The engine becomes a package, not a monolith

Matsya identified a risk that the Scribe did not see from the swan: if all five features are added to `state_machine.py`, that file will grow from ~300 to ~700+ lines — the same accretion pattern that began the fallen machine's collapse.

The new engine lives in a `pipeline/` package with five focused modules, each under 200 lines:

```
pipeline/
  __init__.py    → exports run_pipeline(), the DB-driven entry point
  engine.py      → reads states + transitions from DB, evaluates guards, advances
  contracts.py   → file pattern verification, manifest writing
  escalation.py  → .escalation/<state>/*.md detection + resolution checking
  events.py      → log_phase_event() + sm log --events reader
  seeds.py       → SQL seed data for pipeline_states, transitions, file_contracts
```

`state_machine.py` becomes a thin backward-compatible shim:

```python
def run_with_config(cfg):
    db_path = cfg.get("db_path")
    if db_path and _has_pipeline_tables(db_path):
        from pipeline import run_pipeline
        return run_pipeline(cfg)      # new DB-driven path
    else:
        return _run_hardcoded(cfg)    # existing fallback
```

All existing callers, tests, and deployments without the new tables continue to work unchanged. The hardcoded path is untouched. The new path is a clean import.

### Build order — revised after Matsya's signal

The Fish's build order is more precise than the Scribe's original draft. It is accepted:

| Step | What | Why this order |
|------|------|----------------|
| 1 | Add 4 new tables to `schema.sql` | Foundation. Unblocks everything. |
| 2 | Build `pipeline/events.py` + `sm log --events` | Simplest module. Proves the DB connection. Gives visible output from day one. |
| 3 | Build `pipeline/seeds.py` + update `seed.py` | Populate new tables with current 5-phase topology. |
| 4 | Build `pipeline/engine.py` | The spine. Read states + transitions from DB. Reproduce same behaviour as hardcoded loop. |
| 5 | Build `pipeline/contracts.py` | Hooks into engine after script execution. |
| 6 | Build `pipeline/escalation.py` | Hooks into engine before advance. |
| 7 | ft014 — Parallel fan-out | Only if spine is stable and time remains. Defer otherwise. |
| 8 | Adopt Sprint 02 | Last, once all tables exist. |

Each step is testable before the next begins. No step breaks existing functionality.

### The transition model is lightweight

The DB-driven pipeline is **not** the 11-state monster from the fallen machine. It is a lightweight data representation of the same 5-phase sequence we have today, with one conditional branch at GATE (continue vs. ship).

The `pipeline_transitions` table supports an `is_parallel` column (for ft014) but nothing else. No per-state agent assignment. No frequency modulus. No run-once flags. No arbitrary SQL guard evaluation. The fallen machine proved that each seemingly harmless column creates a combinatorial explosion of state that no single mind can hold.

### ft012 and ft013 hook into the spine after it is stable

File pattern contracts and the escalation mechanism both hook into the engine loop but are not built until `engine.py` is tested and proven. They can be built in either order; they do not depend on each other.

### ft014 is the most speculative feature

Parallel fan-out depends on the transition model's `is_parallel` column. The current 5-phase pipeline has no natural parallel fork. Build ft014 only if the spine is stable and time remains. If deferred, the engine works without it.

### ft015 is built early (table + reader), instrumented later

Matsya's insight: build the `phase_events` table and the `sm log --events` reader second — before the spine — because it is the simplest module and gives something visible from day one. The `log_phase_event()` call sites are added incrementally as each other feature matures.

### Adoption of Sprint 02

Running `sm init` from this directory must detect `sprint/02/` artifacts and prompt to seed Sprint 02 as a `manual`/`completed` sprint entry, the same way Sprint 01 was adopted in Sprint 02.

The adoption note should read:
```
Sprint 02: Durable Execution Log & Project System. 9 features, 73 tests, all verified.
```

### Test strategy

The Scribe omitted a test strategy from the original brief. Matsya will write `sprint/03/test.sh` as he builds each module, since the features require database mocking and filesystem scaffolding that previous sprints did not. Each module is tested before the next begins.

### Existing code that must not break

- `state_machine.py`'s existing `main()` and `run_with_config()` — these must continue to work even without a database. The DB-driven path is an additional capability.
- `sm.py` — all existing commands (`seed`, `run`, `list`, `status`, `log`, `sprint`, `init`, `generate agent`, `list projects`) must continue to work.
- `schema.sql` — the existing tables (`profiles`, `components`, `profile_components`, `sprints`, `phase_runs`) must not be altered. New features add new tables only. No ALTER TABLE on existing tables.
- `config.json` format — unchanged.
- All existing tests must pass after each feature is built.

---

## File Layout Target

### New package structure

```
pipeline/
  __init__.py       → exports run_pipeline(), the new DB-driven entry point
  engine.py         → reads states + transitions from DB, evaluates guards, advances
  contracts.py      → file pattern verification, manifest writing
  escalation.py     → .escalation/<state>/*.md detection + resolution checking
  events.py         → log_phase_event() + sm log --events reader
  seeds.py          → SQL seed data for pipeline_states, transitions, file_contracts
```

### New schema tables

| Table | Purpose |
|-------|---------|
| `pipeline_states` | One row per phase: PLAN, WRITE, REVIEW, COMMIT, GATE |
| `pipeline_transitions` | Directed edges between states, with `guard_expression` and `is_parallel` |
| `file_contracts` | Input/output glob patterns per state |
| `phase_events` | High-resolution event log within phase attempts |

### Seed data target

```
pipeline_states:
  1 | PLAN
  2 | WRITE
  3 | REVIEW
  4 | COMMIT
  5 | GATE

pipeline_transitions:
  PLAN → WRITE
  WRITE → REVIEW
  REVIEW → COMMIT
  COMMIT → GATE
  GATE → PLAN     (guard: backlog_exists)
  GATE → (terminal)  (guard: backlog_empty)

file_contracts:
  PLAN     → output: sprint/*/brief.md
  WRITE    → input: sprint/*/brief.md, output: sprint/*/features.md, output: src/**/*
  REVIEW   → input: sprint/*/features.md, input: src/**/*, output: sprint/*/review.md
  COMMIT   → (no contracts — git commit is self-verifying)
  GATE     → input: backlog/**/*, input: sprint/*/**/*
```

---

## Files the Engineer Should Read First

| File | Why |
|------|-----|
| `signals/matsya-to-saraswati-pipeline-decomposition.md` | Matsya's own proposal for the `pipeline/` package structure and build order |
| `backlog/ft011-db-driven-transitions.md` | Primary feature — the spine |
| `backlog/ft012-file-pattern-contracts.md` | Secondary feature — artifact verification |
| `backlog/ft013-escalation-mechanism.md` | Secondary feature — third exit channel |
| `backlog/ft014-parallel-fan-out.md` | Tertiary feature — engine extension |
| `backlog/ft015-branch-events-audit.md` | Incremental feature — high-res logging |
| `state_machine.py` | The engine that will be refactored — `run_with_config()` becomes a dispatcher |
| `schema.sql` | Existing schema — will add 4 new tables |
| `sm.py` | CLI — needs `sm log --events` flag and `sm run --resume` flag |
| `seed.py` | Will be extended to seed the new tables |
| `sprint/02/brief.md` | Context for Sprint 02 adoption |
| `signals/saraswati-to-matsya-the-spine.md` | Saraswati's blessing on the revised build order |
| `temp/others/sm/daemon.py` | The fallen machine — for reference only. Read the transition/guard/event patterns, do not replicate the complexity. |

---

## Deferred to Sprint 04+

- Parallel fan-out (ft014) — if not completed in Sprint 03
- Profile inheritance (`extends`) — ft007
- Variant creation workflow — ft008
- Component params override system — ft009
- Profile export/import — ft010
- `sm status` rewrite (still reads from env vars/filesystem)
- `sm init --target <path>` for separating DB from code location

---

*Written by Saraswati. Built by Matsya. Watched by Kurma. The wave turns.*
