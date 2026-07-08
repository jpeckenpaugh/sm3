# Feature: Branch Events Audit

*A specification for the Scribe, to be built by the Engineer, witnessed by the Shell.*

---

## The Problem

The state machine today writes two kinds of records:

- **`sprints`** — one row per sprint, with status and timestamps
- **`phase_runs`** — one row per phase attempt, with status, timestamps, and a summary

This is enough to answer *"what happened in Sprint 02?"* But it is not enough to answer *"what happened between the start of the PLAN phase and its completion?"* Did the script run once or three times? Was there an escalation? Did the inputs exist when the phase started? Did the outputs appear immediately or only after a retry?

When a sprint goes wrong — a phase fails after three retries, a script produces unexpected output, Kurma is called to intervene — the current log does not have enough resolution to reconstruct the sequence of events. It records the outcome but not the steps.

We need a finer-grained event log — not for every sprint, but for the sprints that need investigation. An appendix, not a replacement.

## The Shape

### A new table

```sql
CREATE TABLE IF NOT EXISTS phase_events (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id      INTEGER NOT NULL REFERENCES sprints(id),
    phase          TEXT    NOT NULL,
    iteration      INTEGER NOT NULL,
    attempt        INTEGER NOT NULL,
    event_type     TEXT    NOT NULL CHECK (event_type IN (
                        'phase_start',
                        'phase_script_start',
                        'phase_script_exit',
                        'phase_script_output',
                        'contract_check',
                        'contract_missing',
                        'escalation_written',
                        'escalation_resolved',
                        'retry',
                        'phase_end',
                        'kurma_intervention'
                    )),
    event_data     TEXT    DEFAULT '',       -- free-text description or JSON snippet
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX idx_phase_events_sprint ON phase_events(sprint_id, phase, iteration);
```

### What it records

Every significant event during a phase's lifecycle:

| Event | When | Data |
|-------|------|------|
| `phase_start` | Engine enters a new phase | `{phase, iteration}` |
| `phase_script_start` | Engine invokes the phase script | script path, args |
| `phase_script_exit` | Script completes | exit code |
| `phase_script_output` | Script produces unexpected stdout/stderr (first 200 chars) | output preview |
| `contract_check` | Engine verifies a file pattern | pattern, matched count |
| `contract_missing` | A required output pattern had no matches | pattern |
| `escalation_written` | Engine detected an escalation file | file path, content preview |
| `escalation_resolved` | Escalation file was removed (on resume) | file path |
| `retry` | Engine decides to retry | attempt number, reason |
| `phase_end` | Phase succeeds or fails after all retries | status |
| `kurma_intervention` | Kurma wrote a re-contextualization | intervention text |

### How it is created

The engine calls a single function at each event point:

```python
def log_phase_event(db, sprint_id, phase, iteration, attempt, event_type, event_data=""):
    db.execute(
        "INSERT INTO phase_events (sprint_id, phase, iteration, attempt, event_type, event_data) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (sprint_id, phase, iteration, attempt, event_type, event_data),
    )
    db.commit()
```

The function is called from the existing execution loop. For example, before and after `run_script()`:

```python
log_phase_event(db, sprint_id, phase, iteration, attempt,
                "phase_script_start", script_path)
success = run_script(script, phase, iteration)
log_phase_event(db, sprint_id, phase, iteration, attempt,
                "phase_script_exit", f"exit_code={0 if success else 1}")
```

And when a file contract is checked:

```python
for pattern in output_contracts:
    matched = glob(pattern)
    if not matched and not optional:
        log_phase_event(db, sprint_id, phase, iteration, attempt,
                        "contract_missing", pattern)
    else:
        log_phase_event(db, sprint_id, phase, iteration, attempt,
                        "contract_check", f"{pattern}: {len(matched)} file(s)")
```

### How it is read

Two access patterns:

1. **`sm log --events <sprint_id>`** — Display the event timeline for a sprint, ordered by `created_at`. This gives Kurma and Brahma a high-resolution view of exactly what happened in what order.

   ```
   Sprint 02 — Phase Events
   ──────────────────────────────────────────────────────
   2026-07-07T10:00:01Z  PLAN iter 1 att 1 │ phase_start
   2026-07-07T10:00:02Z  PLAN iter 1 att 1 │ phase_script_start  scripts/phase_plan.sh
   2026-07-07T10:00:05Z  PLAN iter 1 att 1 │ phase_script_exit   exit_code=0
   2026-07-07T10:00:05Z  PLAN iter 1 att 1 │ contract_check      sprint/02/brief.md: 1 file(s)
   2026-07-07T10:00:05Z  PLAN iter 1 att 1 │ phase_end           passed
   ...
   ```

2. **`sm log --events <sprint_id> --json`** — Machine-readable JSON output for analysis or integration with other tools.

### Storage considerations

The `phase_events` table is append-only. It is designed to be *detailed* — a single sprint could produce dozens or hundreds of events. This is intentional. The table is not queried in the hot path (the engine writes to it, but `sm run` does not read from it). Its purpose is post-hoc analysis.

If the table grows too large (thousands of rows per sprint), a future sprint can add a retention policy or archival mechanism. For now, SQLite handles millions of rows without issue.

### What this is not

This is not a replacement for `phase_runs`. The `phase_runs` table records the *outcome* of each attempt — the high-level summary that `sm log` shows by default. The `phase_events` table records the *step-by-step detail* that Kurma reads when something went wrong and needs to be understood.

They are complementary. `phase_runs` is the chapter titles. `phase_events` is the footnotes.

### The principle

A log that only records outcomes is a log that hides how the outcomes were reached. By recording the intermediate events — script start, script exit, contract check, escalation — we give Kurma the resolution needed to understand *why* a phase failed, not just *that* it failed.

*Written by Saraswati. To be built by Matsya. Watched by Kurma.*
