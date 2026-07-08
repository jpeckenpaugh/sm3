# Feature: `read_pulse` — Heartbeat at Session Start

*A domain-specific tool for scribes. The Pulse Check made actionable.*

---

## The Problem

The Pulse Check (defined in `trimurti/the-heartbeat-contract.md`) names the ritual: before any shell declares itself ready, it reads the pulse history of the container. Three questions:

1. How many sprints exist?
2. When was the most recent pulse?
3. What is the silence duration?

Currently, a scribe entering PLAN mode has no way to answer these questions. The scribe can read the database schema but cannot run SQL queries. It enters each session blind to the container's history — not knowing how many sprints came before, whether the pipeline is actively running, or how long it has been silent.

## The Tool

A custom tool at `.opencode/tools/read_pulse.ts` backed by `scripts/read_pulse.sh` that reads the project's `matsya.db` and returns the current pulse state.

### Interface

```typescript
tool({
  name: "read_pulse",
  description: "Read the pulse history of the container from the database",
  args: {
    db_path: tool.schema.string().optional().describe("Path to matsya.db (auto-detected if not provided)"),
  },
  execute: async (args, context) => {
    // Invokes: bash scripts/read_pulse.sh [--db <path>]
  }
})
```

### Return format

```json
{
  "sprint_count": 4,
  "active_sprint": {
    "number": 4,
    "status": "active",
    "started_at": "2026-07-08T12:00:00Z"
  },
  "last_pulse": {
    "timestamp": "2026-07-08T15:36:19Z",
    "phase": "TEST_RUN",
    "status": "escalation_written",
    "sprint_number": 4
  },
  "silence_duration_seconds": 1847,
  "silence_duration_human": "30m 47s",
  "dispatch_count": 7,
  "phase_count": 35,
  "db_path": "/root/sm/matsya.db"
}
```

### Backing script: `scripts/read_pulse.sh`

```bash
#!/bin/bash
DB="${1:-matsya.db}"

if [ ! -f "$DB" ]; then
  echo '{"error": "Database not found: '"$DB"'"}'
  exit 1
fi

sqlite3 -json "$DB" "
SELECT
  (SELECT COUNT(*) FROM sprints) AS sprint_count,
  (SELECT json_object('number', number, 'status', status, 'started_at', started_at)
   FROM sprints ORDER BY id DESC LIMIT 1) AS active_sprint,
  (SELECT json_object('timestamp', completed_at, 'phase', phase, 'status', status)
   FROM phase_runs ORDER BY id DESC LIMIT 1) AS last_phase,
  (SELECT COUNT(*) FROM dispatch_log) AS dispatch_count,
  (SELECT COUNT(*) FROM phase_runs) AS phase_count
" 2>/dev/null
```

### Permission

```yaml
permission:
  "*": deny
  read: allow
  edit:
    "*.md": allow
    ...
  read_pulse: allow       # <-- added to scribe profiles
```

## Integration with PLAN Mode

The mode-specific component for scribe-PLAN should include:

```markdown
### 1. Read the Pulse

Before planning, call `read_pulse` to understand the container's state:
- How many sprints have completed?
- Is there an active sprint?
- When was the last phase run?
- How long has the container been silent?

Include this pulse data in your sprint brief so the team knows
the state of the container at planning time.
```

## Integration with the CONFIRM_BOOTSTRAP Handshake

The Pulse Check ritual (Mahadevi's naming) becomes automated:

```python
# In dispatch.py, before the handshake response is returned:
pulse = read_pulse(db_path)
response_text = f"""BOOTSTRAP CONFIRMED.

Before speaking, I read the pulses of this container:
  Sprints completed: {pulse.sprint_count}
  Last phase pulse:  {pulse.last_pulse.timestamp}
  Silence duration:  {pulse.silence_duration_human}

I have witnessed what happened while I was absent.
Available MODE_FLAG values are CONFIRM_BOOTSTRAP, {mode_flag}
"""
```

## What it enables

| Before | After |
|--------|-------|
| A scribe enters PLAN mode knowing nothing about the container's history | The scribe sees the pulse immediately — how many sprints, when was the last phase, how long the silence |
| The Pulse Check is a manual ritual the shell must remember to perform | The pulse is read automatically at session start and included in CONFIRM_BOOTSTRAP |
| The sprint brief has no context about previous sprints' pace | The brief can reference pulse data: "4 sprints completed, last pulse 30m ago" |

---

*Specified by Saraswati. Built by Matsya. Used by scribe agents. Watched by Kurma.*
