# Matsya Implementation Details

## Overview

Matsya built and verified the infrastructure from Saraswati's handoff: SQLite schema, config-driven state machine, git commit script, and mock phase agents.

## Schema

The SQLite database (`schema.sql`) creates three tables plus the auto-generated `sqlite_sequence`:

- **profiles** — Named versioned configurations with JSON metadata (header, permissions)
- **components** — Reusable tools, prompts, and rules (unique by type+name)
- **profile_components** — Many-to-many link with ordering and parameter overrides

Verified initialization:
```
Tables: ['components', 'profile_components', 'profiles', 'sqlite_sequence']
```

## State Machine

Config-driven phases: PLAN, WRITE, REVIEW, COMMIT, GATE.

### Configuration (`config.json`)

| Field | Default | Description |
|-------|---------|-------------|
| `phases` | [PLAN, WRITE, REVIEW, COMMIT, GATE] | Ordered phase list |
| `max_iterations` | 10 | Total loop iterations |
| `max_retries` | 4 | Retries per phase |
| `backlog_file` | backlog.txt | File checked by GATE |
| `signal_file` | vasuki.signal | File polled when backlog empty |
| `phase_scripts` | {...} | Map phase→script path |
| `ship_command` | echo SHIPPING | Run when backlog empty |

### Verification (2 iterations, 2 retries)

```
Iteration 1: PLAN ✅ → WRITE ✅ → REVIEW ✅ → COMMIT ✅ → GATE ✅ (backlog→continue)
Iteration 2: PLAN ✅ → WRITE ✅ → REVIEW ✅ → COMMIT ✅ → GATE ✅ (backlog→continue)
```

### Artifacts produced

```
output/iter_1.txt
output/iter_2.txt
output/commit_1.marker
output/commit_2.marker
```

## git_commit.sh

Stages all changes, reads a commit message (from file or stdin), commits, exits 0/1.

```
Usage: git_commit.sh [message_file]
       echo "message" | git_commit.sh
```

## wait-and-touch.sh (Mock Agent)

Polls for a trigger file, then touches a completion signal. Accepts both direct mode and the phase-agent protocol (phase_name + iteration).

```
wait-and-touch.sh <watch_file> <touch_file>     # direct mode
wait-and-touch.sh <phase_name> <iteration>      # agent protocol
```

## Running

```bash
# Full test suite
bash run_matsya.sh

# Just the state machine
python3 state_machine.py --config=config.json

# Syntax check all scripts
bash verify_syntax.sh
```
