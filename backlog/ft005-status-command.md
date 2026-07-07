# Feature: Status Command

*A concept for the Builder to interpret.*

---

## The Problem

The state machine runs through iterations and phases, but there is no easy way to see *where things stand right now* — what iteration is active, what phase completed last, whether the backlog is empty, or if there's an active signal.

## The Goal

`sm status` provides a snapshot of the current system state: the active or last-completed iteration and phase, backlog status, and any pending signals.

## The Shape

The command gathers its information from multiple sources:

- **State file or DB table**: The state machine should persist its progress (current iteration, current phase, last action) somewhere queryable. This could be a simple JSON state file, or a new `state` table in SQLite.
- **Backlog**: Check whether `backlog/` directory exists and count its contents.
- **Signal file**: Check whether `vasuki.signal` exists.

Example output:

```
Matsya State Machine — Status
──────────────────────────────
Iteration:     3 of 10
Phase:         WRITE (attempt 2/4)
Backlog:       4 feature files
Signal:        absent
Last commit:   abc1234 "Implemented ENGINEER phase scripts"
```

If no state file exists yet (fresh clone, never run):

```
Matsya State Machine — Status
──────────────────────────────
State:         Never run — seed and run to begin
```

## What the Builder Must Decide

- Where to persist runtime state — a new `state` SQLite table? A JSON file? Environment variables?
- Whether `state_machine.py` writes its state as it progresses, or `sm status` infers it from filesystem artifacts
- How to display "not started" vs "in progress" vs "completed" states
- Whether to show the active profile name (if `sm run --profile` was used)

## Open Question

Should the status command be purely read-only, or should it support `--reset` to clear state and start fresh? That's a separate feature, but worth noting as a likely future addition.

---

*The Scribe maps the territory. The Builder walks it.*
