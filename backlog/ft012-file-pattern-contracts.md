# Feature: File Pattern Contracts

*A specification for the Scribe, to be built by the Engineer, witnessed by the Shell.*

---

## The Problem

Today, each phase in the state machine executes a shell script and trusts that script to produce the right artifacts. The engine does not know what the script is supposed to produce. It cannot verify that the output is complete. It cannot tell Saraswati or Kurma what artifacts were created or left missing.

The scripts are black boxes. The handoff between phases is implicit — whatever one script leaves on disk, the next script is expected to find. When a script fails to produce a file, the failure is silent until a downstream script crashes.

We need a way for the state machine to know, for each phase:
- What files does this phase consume?
- What files does this phase produce?
- Were all expected outputs created?

## The Shape

### A new table

```sql
CREATE TABLE IF NOT EXISTS file_contracts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    state_name  TEXT    NOT NULL,
    direction   TEXT    NOT NULL CHECK (direction IN ('input', 'output')),
    pattern     TEXT    NOT NULL,
    description TEXT    DEFAULT '',
    optional    INTEGER NOT NULL DEFAULT 0
);
```

Each row declares that a given phase expects to consume (`input`) or promises to produce (`output`) files matching a glob pattern.

### Seed data for the current 5-phase pipeline

```sql
-- PLAN produces a brief
INSERT INTO file_contracts (state_name, direction, pattern, description)
VALUES ('PLAN', 'output', 'sprint/*/brief.md', 'Sprint brief document');

-- WRITE consumes the brief, produces features and code
INSERT INTO file_contracts (state_name, direction, pattern, description)
VALUES ('WRITE', 'input', 'sprint/*/brief.md', 'Sprint brief');
INSERT INTO file_contracts (state_name, direction, pattern, description)
VALUES ('WRITE', 'output', 'sprint/*/features.md', 'Feature list');
INSERT INTO file_contracts (state_name, direction, pattern, description)
VALUES ('WRITE', 'output', 'src/**/*', 'Source files');

-- REVIEW consumes what WRITE produced
INSERT INTO file_contracts (state_name, direction, pattern, description)
VALUES ('REVIEW', 'input', 'sprint/*/features.md', 'Feature list');
INSERT INTO file_contracts (state_name, direction, pattern, description)
VALUES ('REVIEW', 'input', 'src/**/*', 'Source files');
INSERT INTO file_contracts (state_name, direction, pattern, description)
VALUES ('REVIEW', 'output', 'sprint/*/review.md', 'Review report');

-- COMMIT produces a git commit (no file pattern needed, or just a marker)
-- GATE consumes the sprint artifacts and the backlog
INSERT INTO file_contracts (state_name, direction, pattern, description)
VALUES ('GATE', 'input', 'backlog/**/*', 'Backlog features');
INSERT INTO file_contracts (state_name, direction, pattern, description)
VALUES ('GATE', 'input', 'sprint/*/**/*', 'Sprint artifacts');
```

### What the engine does with this

During each phase execution, **after** the phase script completes:

1. **Verify outputs.** For each `output` contract belonging to the current state, glob the pattern under the project root. Log which patterns matched and which did not. Missing outputs that are not marked `optional` produce a warning (but do not fail the phase — the VERIFY step decides success or failure).

2. **Stage for handoff.** After verification, write a small JSON manifest to `sprint/<N>/.contracts/<state>.json` listing the resolved paths for each input and output pattern. The next phase's script can read this manifest to know exactly which files it should consume.

3. **Report to Kurma.** The verification results are logged to the `phase_runs` output_summary so that Kurma can read them and see whether the artifact flow is healthy.

### What this enables

- **Explicit artifact boundaries.** Saraswati can see, at a glance, what each phase produces and consumes. The handoff between phases is no longer implicit.

- **Early warning.** If a phase completes but its expected outputs are missing, the engine surfaces this immediately rather than letting the next phase crash.

- **Audit trail.** After a sprint completes, the file contracts tell you exactly what was produced, by which phase, and whether anything was missing.

- **A pattern for escalation.** In a future sprint, if an output is missing and the phase cannot retry, the engine can write an escalation file — signalling Kurma that the artifact chain is broken.

### What this is not

This is not a build system. The engine does not track file hashes, detect incremental changes, or skip phases based on input staleness.

This is not a replacement for the phase scripts. The scripts still do the actual work. The contracts only describe what the work is expected to produce — and verify that it did.

### Backward compatibility

If the `file_contracts` table is empty or does not exist, the engine skips all contract verification and behaves exactly as it does today. The feature is additive — it only activates when data is seeded.

### The principle

A phase should declare what it needs and what it leaves behind — not as documentation for humans, but as data the engine can verify. The contract is the handoff made visible.

*Written by Saraswati. To be built by Matsya. Watched by Kurma.*
