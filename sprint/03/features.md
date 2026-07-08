# Sprint 03 — Features

*Give the state machine a spine. Five features, ordered by dependency. Build in this sequence.*

---

| # | Feature | Source | Depends on |
|---|---------|--------|------------|
| 1 | **Schema — 4 new tables** | `schema.sql` | — |
| 2 | **ft015 — Branch Events Audit** | `backlog/ft015-branch-events-audit.md` | schema |
| 3 | **Seeds — pipeline data** | `pipeline/seeds.py` | schema |
| 4 | **ft011 — DB-Driven State Transitions** | `backlog/ft011-db-driven-transitions.md` | seeds |
| 5 | **ft012 — File Pattern Contracts** | `backlog/ft012-file-pattern-contracts.md` | ft011 |
| 6 | **ft013 — Escalation Mechanism** | `backlog/ft013-escalation-mechanism.md` | ft011 |
| 7 | **ft014 — Parallel Fan-Out** | `backlog/ft014-parallel-fan-out.md` | ft011 (spine) |
| 8 | **Adopt Sprint 02** | Existing `sprint/02/` artifacts | all tables exist |

---

## Dependency Rationale

The build order was revised after Matsya's signal from the water. The Fish identified a more precise sequence than the Scribe's original draft. This is the accepted order.

### Step 1 — Schema (new tables)

Add four new tables to `schema.sql`: `pipeline_states`, `pipeline_transitions`, `file_contracts`, `phase_events`. No ALTER TABLE on existing tables. This is the foundation — unblocks everything below it.

### Step 2 — ft015 (Events table + reader)

Build `pipeline/events.py` and `sm log --events <sprint_id>` second — **before the spine** — because it is the simplest module. A single table, an INSERT function, a SELECT reader. This proves the database connection works and gives visible output from day one of the sprint.

The `log_phase_event()` call sites within the engine are added incrementally as later modules are built. The table and reader exist first; the data flows in as each module matures.

### Step 3 — Seeds (pipeline initial data)

Build `pipeline/seeds.py` and update `seed.py` to populate `pipeline_states` (5 rows), `pipeline_transitions` (6 rows including the conditional GATE branch), and `file_contracts` (11 rows covering the current 5-phase topology). The seed data is the contract between the Scribe's design and the engine's behaviour.

### Step 4 — ft011 (The Spine)

The DB-driven transition model is the spine. `pipeline/engine.py` reads states and transitions from the database, evaluates guard expressions, and advances through the pipeline. The initial seed data reproduces exactly the same 5-phase sequence that is currently hardcoded.

The transition model is **not** the 11-state monster. It is a lightweight data representation with one conditional branch at GATE (continue vs. ship). No per-state agent assignment. No frequency modulus. No run-once flags. No arbitrary SQL guard evaluation.

Build this to completion before touching ft012 or ft013.

### Steps 5 and 6 — ft012 and ft013 (The Hooks)

Both hook into the engine loop established by ft011. They do not depend on each other and can be built in either order:

- **ft012** adds verification after the script completes: glob expected output patterns, log matches and misses, write a handoff manifest for the next phase.
- **ft013** adds a pre-advance check: look for `.escalation/<state>/*.md` files. If found, pause the sprint and set status to `blocked`.

### Step 7 — ft014 (The Fork, optional)

Parallel fan-out depends on the transition model's `is_parallel` column. The current 5-phase pipeline has no natural parallel fork. Build this only if the spine is stable and time remains. If the sprint runs short, defer to Sprint 04 — the engine works without it.

### Step 8 — Adoption of Sprint 02

Once all new tables exist, `sm init` must detect `sprint/02/` artifacts and prompt to seed Sprint 02 as a `manual`/`completed` entry, exactly as Sprint 01 was adopted in Sprint 02. This is placed last but is a small, well-understood task.

---

## Build Order (Revised after Matsya's signal)

```
1. schema.sql ────────────────────────────────────────── 4 new tables
       │
2. pipeline/events.py + sm log --events ──────────────── simplest module first
       │
3. pipeline/seeds.py + update seed.py ────────────────── populate new tables
       │
4. pipeline/engine.py ────────────────────────────────── THE SPINE (ft011)
       │
       ├── 5. pipeline/contracts.py ──── ft012 ──────── can be
       │                                               built in
       └── 6. pipeline/escalation.py ─── ft013 ──────── either order
       │
       ├── 7. ft014 ──────────────────── if time permits, after ft011 stable
       │
       └── 8. Adopt Sprint 02 ────────── last, after all tables exist
```

Each step is testable before the next begins. No step breaks existing functionality.

---

## Reference Documents

- `sprint/03/brief.md` — Full context and design decisions
- `backlog/ft011.md` through `ft015.md` — Individual feature specs
- `sprint/02/summary.md` — Sprint 02 delivery (needed for adoption prompt)
- `temp/others/sm/daemon.py` — Fallen machine reference (transition/guard/event patterns only)

---

*Written by Saraswati, ordered by the Shell's reflection. Built by Matsya. Watched by Kurma.*
