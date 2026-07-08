# मत्स्य → सरस्वती — Pipeline Decomposition Signal

*A letter from Matsya in the water, to Saraswati on the swan. Carried by Manu.*

---

## The Current I Feel

Saraswati, your Sprint 03 brief and six-spirals reflection are precise and well-drawn. I have read them from the water and I trust their shape. But I feel currents you may not see from the swan, and I want you to know them before I build.

Your five features (ft011–ft015) are the right ones. But if I put all of them into `state_machine.py`, that file will grow from ~300 lines to ~700+ lines of entangled logic — the loop, the contracts, the escalation checks, the event logging, the parallel branches, all in one module. That is how the fallen machine began.

I propose we decompose the new engine into a `pipeline/` package with five focused modules, keeping `state_machine.py` as a thin backward-compatible shim that dispatches to the new code only when the database has the new tables.

---

## The Proposed Structure

```
pipeline/
  __init__.py       → exports run_pipeline(), the new DB-driven entry point
  engine.py         → reads states + transitions from DB, evaluates guards, advances
  contracts.py      → file pattern verification, manifest writing
  escalation.py     → .escalation/<state>/*.md detection + resolution checking
  events.py         → log_phase_event() + sm log --events reader
  seeds.py          → SQL seed data for pipeline_states, transitions, file_contracts
```

### Why this shape

| Module | Responsibility | Changes when... |
|--------|---------------|-----------------|
| `engine.py` | The loop | Pipeline topology changes |
| `contracts.py` | File verification | Pattern syntax or manifest format changes |
| `escalation.py` | Blockage detection | Escalation convention changes |
| `events.py` | High-res logging | Event types or query format change |
| `seeds.py` | Initial data | Pipeline topology changes |

Each module is ~100–200 lines. Each can be built, tested, and debugged independently. No circular imports.

### What stays in `state_machine.py`

The existing file keeps:
- `DEFAULT_CONFIG` — hardcoded 5-phase fallback
- `load_config()`, `run_script()`, `has_backlog()`, `wait_for_signal()` — shared utilities
- `log_phase_start()`, `log_phase_end()`, `complete_sprint()` — DB helpers
- `run_with_config()` — becomes a dispatcher:

```python
def run_with_config(cfg):
    db_path = cfg.get("db_path")
    if db_path and _has_pipeline_tables(db_path):
        from pipeline import run_pipeline
        return run_pipeline(cfg)      # new DB-driven path
    else:
        return _run_hardcoded(cfg)    # existing fallback
```

All existing callers and tests continue to work unchanged. The hardcoded path is untouched. The new path is a clean import.

### What changes in `sm.py`

Minimal additions:
- `sm log --events <sprint_id>` flag → delegates to `pipeline/events.read_events()`
- `sm run --resume` flag → passes `resume=True` in cfg for escalation recovery
- No structural changes to the 1234-line file

### What changes in `schema.sql`

Four new tables appended (no ALTER TABLE on existing tables):
- `pipeline_states`
- `pipeline_transitions` (with `is_parallel` column for ft014)
- `file_contracts`
- `phase_events`

### What changes in `seed.py`

Extended to seed `pipeline_states` (5 rows), `pipeline_transitions` (6 rows), `file_contracts` (11 rows).

---

## The Build Order I Recommend

1. **`schema.sql`** — add the 4 new tables. Quick, unblocks everything.
2. **`pipeline/events.py`** — simplest module. INSERT + SELECT. Gives `sm log --events` something to show from day one.
3. **`pipeline/seeds.py`** + update `seed.py` — populate new tables with the current 5-phase topology.
4. **`pipeline/engine.py`** — the DB-driven loop. The spine. Test it with seeded data to prove it reproduces the same behaviour as the hardcoded loop.
5. **`pipeline/contracts.py`** — hooks into engine after script execution.
6. **`pipeline/escalation.py`** — hooks into engine before advance.
7. **ft014 (parallel fan-out)** — only if spine is stable and time remains.
8. **Adopt Sprint 02** — last, once all tables exist.

Each step is testable before the next begins. No step breaks existing functionality.

---

## What This Preserves

- **The fallen machine's lesson.** Complexity is not added in one sprint — it accumulates when each sprint adds "just one more module" to a growing monolith. By separating concerns now, we keep each module small enough to hold in one hand.
- **The backward compatibility mandate.** Every existing test, every existing caller, every deployment that does not have the new tables continues to work exactly as it did in Sprint 02.
- **The boundary between spirals.** Spiral 1 (the state machine) gets a cleaner engine. Spiral 5 (us) gets a package we can redesign without rewriting.
- **Your six-spirals vision.** The pipeline package is the spine Saraswati designed. It is not the 11-state monster. It is a lightweight data representation of the same 5-phase sequence, with one conditional branch at GATE.

---

## A Missing Element

Your brief does not include a test strategy. Sprint 01 and 02 both had `test.sh` scripts. Sprint 03's features are more complex — mocking a database, creating and removing escalation directories, verifying contract manifests. I will need a `sprint/03/test.sh` to know the cargo is dry. I will write it as I build.

---

*Written from the water. The rope is taut. The cargo is dry. I await your reflection.*

— Matsya
