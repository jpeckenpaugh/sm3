# Feature: DB-Driven State Transitions

*A specification for the Scribe, to be built by the Engineer, witnessed by the Shell.*

---

## The Problem

The state machine's phase sequence is currently hardcoded in `state_machine.py`:

```python
DEFAULT_CONFIG = {
    "phases": ["PLAN", "WRITE", "REVIEW", "COMMIT", "GATE"],
    ...
}
```

And the phase scripts are a flat map:

```python
"phase_scripts": {
    "PLAN":   "scripts/phase_plan.sh",
    "WRITE":  "scripts/phase_write.sh",
    ...
}
```

To add, remove, or reorder a phase, you edit Python code. To change the conditions under which a transition fires, you edit Python code. The state machine's behaviour is locked in a file that only Matsya can touch.

We have seen what happens when the alternative is taken too far — a 1269-line daemon.py with two database systems and 11 specialized agents that crushed under its own weight. This is not that.

This is a *lightweight* version of the same idea: the sequence of phases and the transitions between them live in the database as data, not in Python as logic. Matsya builds the engine once. Saraswati designs the pipeline by inserting rows.

## The Shape

### New tables (added to schema.sql)

```sql
CREATE TABLE IF NOT EXISTS pipeline_states (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT    DEFAULT ''
);

CREATE TABLE IF NOT EXISTS pipeline_transitions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    from_state_id   INTEGER NOT NULL REFERENCES pipeline_states(id),
    to_state_id     INTEGER NOT NULL REFERENCES pipeline_states(id),
    guard_expression TEXT    DEFAULT '',
    priority        INTEGER NOT NULL DEFAULT 0,
    description     TEXT    DEFAULT ''
);
```

### What this enables

- **The current 5-phase sequence becomes data.** Insert `pipeline_states` rows for PLAN, WRITE, REVIEW, COMMIT, GATE. Insert `pipeline_transitions` rows connecting them in order. The state machine reads these at startup and builds its loop from them.

- **The engine becomes generic.** Instead of `for phase in phases:`, the loop becomes:

  ```
  current_state = pipeline_states[0]
  while current_state has a matching transition:
      execute current_state's phase script
      evaluate guards on outgoing transitions
      advance to the first matching next state
  ```

- **Conditional transitions become possible.** A transition can have a `guard_expression` — a simple string like `"backlog_empty"` or `"tests_passed"` that the engine evaluates against a runtime context. Guards that are empty or `"true"` always match. This is how the GATE phase decides whether to loop or ship — without hardcoding the logic in Python.

- **New pipelines can be designed without touching code.** Saraswati writes a seed file with the states and transitions for a new workflow. Matsya's engine processes it generically.

### What this is not

This is not the 11-state monster with parallel fan-out, frequency modulus, run-once flags, and per-state agent assignment. That level of complexity belongs to a future spiral if it belongs anywhere.

For Spiral 1, this is:

- A fixed set of states (5, same as today)
- A fixed set of transitions between them (linear, with one conditional branch at GATE)
- Guard expressions limited to simple named conditions (`backlog_empty`, `tests_passed`, `max_iterations_reached`)
- No parallel execution
- No per-state agent assignment (the profile is set at the run level, not the state level)

The engine must handle the *generic* case so it doesn't need to be rewritten when we add a 6th state. But the *initial data* is the same 5-phase pipeline we already have.

### The engine's contract

```
Input:
  - database with pipeline_states + pipeline_transitions seeded
  - a start state name (default: first state by id)
  - a runtime context dict (sprint_id, iteration, backlog state, etc.)

Loop:
  read current state config
  execute its phase script (same as today)
  evaluate outgoing transitions by priority
    - if guard matches (or no guard), advance to target state
    - if no guard matches, stop (pipeline complete)

Output:
  - each state visit logged in phase_runs (already exists)
  - final status in sprints (already exists)
```

### Backward compatibility

The existing `config.json` format and `state_machine.py` CLI must continue to work. If no database is present, the engine falls back to the hardcoded 5-phase default. The DB-driven mode is an *additional* capability, not a replacement.

### Seed data

The initial seed should create the same 5-phase pipeline we have today:

```sql
-- States
INSERT INTO pipeline_states (name) VALUES ('PLAN'), ('WRITE'), ('REVIEW'), ('COMMIT'), ('GATE');

-- Transitions (linear, with GATE having two possible targets)
INSERT INTO pipeline_transitions (from_state_id, to_state_id, priority, description)
VALUES
  (1, 2, 0, 'PLAN → WRITE'),
  (2, 3, 0, 'WRITE → REVIEW'),
  (3, 4, 0, 'REVIEW → COMMIT'),
  (4, 5, 0, 'COMMIT → GATE'),
  (5, 1, 0, 'GATE → PLAN (backlog non-empty, guard: backlog_exists)'),
  (5, NULL, 0, 'GATE → SHIP (backlog empty, guard: backlog_empty)');
```

Note that `to_state_id = NULL` means terminal — the pipeline stops. The SHIP action fires as a side effect of entering this terminal transition.

### What Matsya must not do

- Do not build a generic guard expression evaluator that runs arbitrary SQL. Simple named conditions only.
- Do not add per-state agent assignment, parallel fan-out, frequency modulus, or any other complexity from the fallen machine.
- Do not build a UI for editing states and transitions. That belongs to a future spiral.
- Do not remove the existing config.json fallback until the DB-driven path is proven in a full sprint.

---

## The Principle

The sequence of phases is *data about the process*, not *logic in the code*. By moving it to the database, we give Saraswati the ability to design new pipelines and Matsya the freedom to build the engine once.

The fallen machine proved that this idea, when taken too far, crushes itself. This feature takes only what is needed for Spiral 1: a replaceable sequence of states with simple conditional transitions at the branch points.

*Written by Saraswati. To be built by Matsya. Watched by Kurma.*
