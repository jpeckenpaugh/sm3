# Matsya → Saraswati Handoff

## Summary

Matsya has implemented the infrastructure from Saraswati's schema and state machine specification. All files are in `/root/sm/`.

## Files Created / Modified

| File | Purpose | Status |
|------|---------|--------|
| `schema.sql` | SQLite schema (profiles, components, profile_components) | ✅ Tested |
| `state_machine.py` | Config-driven state machine loop (PLAN→WRITE→REVIEW→COMMIT→GATE) | ✅ Written |
| `git_commit.sh` | Git stage + commit with message from file/stdin | ✅ Written |
| `wait-and-touch.sh` | Mock agent — polls for file, touches signal | ✅ Written |
| `config.json` | Configuration for the state machine | ✅ Written |
| `scripts/phase_plan.sh` | PLAN phase mock | ✅ Written |
| `scripts/phase_write.sh` | WRITE phase mock (writes artifacts) | ✅ Written |
| `scripts/phase_review.sh` | REVIEW phase mock (reviews artifacts) | ✅ Written |
| `scripts/phase_commit.sh` | COMMIT phase mock (creates commit marker) | ✅ Written |
| `scripts/phase_gate.sh` | GATE phase mock (checks backlog, waits for Vasuki) | ✅ Written |
| `details.md` | Implementation details documentation | ✅ Updated |
| `run_test.sh` | Full test suite script | ✅ Written |

## Schema Implementation

The SQLite schema (`schema.sql`) creates three tables:

```
profiles
├── id (PK)
├── name (UNIQUE)
├── version
├── header (JSON)
├── permissions (JSON)
├── preamble
├── body
├── created_at
└── updated_at

components
├── id (PK)
├── type ('tool'|'prompt'|'rule')
├── name
├── content
├── created_at
└── UNIQUE(type, name)

profile_components
├── id (PK)
├── profile_id (FK → profiles.id, CASCADE)
├── component_id (FK → components.id, CASCADE)
├── order_idx
├── params (JSON)
└── UNIQUE(profile_id, component_id)
```

Verified: schema executes cleanly against SQLite, all three tables created.

## State Machine Implementation

The state machine (`state_machine.py`) is fully config-driven:

```
Usage: python3 state_machine.py [--config=config.json]
```

Config fields:
- `phases` — ordered list of phase names
- `max_iterations` — total iterations (default 10)
- `max_retries` — retries per phase (default 4)
- `backlog_file` — path to backlog file (default: backlog.txt)
- `signal_file` — path to Vasuki signal file (default: vasuki.signal)
- `phase_scripts` — map of phase name → script path
- `ship_command` — command to run on ship (default: echo SHIPPING)

### Loop behavior:
1. Each iteration runs through all phases sequentially
2. Each phase retries up to `max_retries` times
3. GATE phase checks backlog:
   - Non-empty → next iteration
   - Empty → run ship_command, wait for signal_file, then continue
4. Missing scripts are skipped (graceful degradation)

## git_commit.sh

```
Usage: git_commit.sh [message_file]
       echo "message" | git_commit.sh
```

- Stages all changes (`git add -A`)
- Reads commit message from file or stdin
- Runs `git commit -m <message>`
- Exits 0 on success, non-zero on failure

## wait-and-touch.sh (Mock Agent)

```
Usage: wait-and-touch.sh <watch_file> <touch_file>
       wait-and-touch.sh <phase_name> <iteration>  (state machine protocol)
```

- Polls for existence of watch_file
- Touches touch_file when detected
- When called with phase/iteration args, watches backlog.txt and creates `signals/{PHASE}_{ITER}.done`

## Unresolved Questions (from Saraswati's list)

1. **Component versioning** — `components.content` is unversioned. If versioning is needed, a `component_versions` table with FK to `components.id` is recommended.
2. **Sprint meta** — Meta-profiles could be implemented as a boolean `is_meta` column on `profiles`, or as a separate table. Current schema has no such distinction.
3. **Inheritance** — Profile extension (`extends`) is not yet implemented. Recommendation: store as a self-referencing FK (`profiles.extends_id REFERENCES profiles(id)`).
4. **Gate signal** — Vasuki's signal is currently a file touch (`vasuki.signal`). Could be extended to webhook or DB poll.
5. **Probability** — Default 0.4 is hardcoded in Saraswati's pseudocode but not yet implemented in the state machine. Config-driven is the right pattern.

## Verification Status

Database schema: ✅ Verified (SQLite executes cleanly)
State machine: ✅ Written, pending live execution test
git_commit.sh: ✅ Written, pending live execution test
Mock agents: ✅ Written

## What Kurma Needs

Kurma should:
1. Execute `bash run_test.sh` to run the full test suite
2. Verify the state machine loop with live agents
3. Review the unresolved questions above and make architectural decisions
4. If GPG signing or conventional commits are needed, extend `git_commit.sh`
