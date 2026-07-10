# Debug 02: `--profile` Is Misleading on `sm run`

*Found by Kurma after Sprint 07. Confirmed by Vasuki.*

---

## The Bug

`sm run --profile <name>` requires `--profile` (`required=True` at `cli.py` line 1439). This forces the user to specify an agent profile (e.g. `scribe`, `builder`, `warden`) when starting a pipeline run.

But **the pipeline engine already knows which agent to dispatch for each state**. Since Sprint 03, `pipeline_states.agent_name` stores the correct agent per state:

```
pipeline_states:
  PLAN       → agent_name: scribe-PLAN
  WRITE      → agent_name: builder-ENGINEER
  REVIEW     → agent_name: warden-REVIEW
  TEST_BUILD → agent_name: builder-TEST
  TEST_RUN   → agent_name: warden-TEST_RUN
  SPRINT_GATE → agent_name: warden-GATE
```

The `--profile` flag is **redundant** for the pipeline-driven execution path. Worse, it is **misleading** — it implies the user must pick a single agent, when in fact the pipeline auto-resolves the correct agent for each phase from the database.

### What Happens Today

```bash
# User thinks: "I pick which agent runs the whole sprint"
sm run --profile scribe-PLAN

# But the engine actually resolves agents per state from pipeline_states:
# PLAN  → scribe-PLAN   (matches --profile, coincidentally)
# WRITE → builder-ENGINEER  (ignores --profile)
# REVIEW → warden-REVIEW    (ignores --profile)
```

### What Should Happen

```bash
# No --profile needed at all
sm run

# Engine reads pipeline_states, resolves agent per state, dispatches correctly
```

---

## The Code

**Location:** `cli.py` line 1438–1439:

```python
p_run = subparsers.add_parser("run", help="Load a profile and start the state machine loop (auto-creates sprint)")
p_run.add_argument("--profile", required=True, help="Profile name to load")
```

**The `cmd_run()` function** (line 205) currently uses `--profile` for two things:
1. Loading the profile's permissions and body to pass to the state machine
2. Setting `MATSYA_PROFILE` env var for phase scripts

When the pipeline is driven by `pipeline_states.agent_name`, item 1 is no longer needed — the pipeline reads the profile from the database per state. Item 2 (`MATSYA_PROFILE`) is only needed if a phase script explicitly reads that env var, which the DB-driven pipeline does not.

---

## The Fix

### 1. Remove `--profile` from `sm run` entirely

Delete the line:

```python
# Before — DELETE this line:
p_run.add_argument("--profile", required=True, help="Profile name to load")
```

The `run` parser no longer accepts `--profile` at all. Profiles are resolved per-state by the pipeline engine from `pipeline_states.agent_name`.

### 2. Update the parser help text

```python
# Before:
p_run = subparsers.add_parser("run", help="Load a profile and start the state machine loop (auto-creates sprint)")

# After:
p_run = subparsers.add_parser("run", help="Start a pipeline-driven sprint (resolves agents per state from database)")
```

### 3. Update `cmd_run()` to remove profile-loading dependency

The `cmd_run()` function currently opens a DB connection, loads a profile, auto-creates a sprint, then passes the profile data to the state machine. After removing `--profile`, the function must:

1. Auto-create the sprint (same as before)
2. Pass `db_path` and `sprint_id` to `run_with_config()` (same as before)
3. **Skip** the profile-loading block entirely — no `SELECT FROM profiles`, no component assembly, no `MATSYA_PROFILE`/`MATSYA_HEADER`/`MATSYA_BODY`/`MATSYA_PERMISSIONS` env vars
4. `cfg["profile"]` is no longer set — the pipeline engine resolves the agent from `pipeline_states` per state

Remove the following from `cmd_run()`:
- Lines 213–244: profile load, component assembly, body construction
- Lines 286–292: `cfg["profile"]` assignment
- Lines 300–303: `os.environ` env var settings
- Lines 305–309: profile info print statements

### 4. Update `run_with_config()` in `state_machine.py`

The function receives `cfg` without a `cfg["profile"]` key. Update `state_machine.py` to handle this:

```python
# Before (expects profile in config):
profile_data = cfg.get("profile", {})

# After (profile resolved from pipeline_states per state):
# The engine reads pipeline_states.agent_name and loads the profile
# from the database at each state transition. No profile needed at startup.
```

---

## What Remains in `cmd_run()` After the Change

```python
def cmd_run(args):
    """Start a pipeline-driven sprint without requiring a profile."""
    db_path = get_db_path(args.db)
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()

        # Ensure sprints table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sprints'"
        )
        if not cursor.fetchone():
            print("✗ Database schema missing 'sprints' table. Run 'sm seed' to update.")
            sys.exit(1)

        # Auto-create sprint (driven mode)
        cursor.execute("SELECT COALESCE(MAX(number), 0) + 1 FROM sprints")
        next_num = cursor.fetchone()[0]
        now = _now_utc()
        cursor.execute(
            """INSERT INTO sprints (number, mode, status, started_at, notes)
               VALUES (?, 'driven', 'active', ?, ?)""",
            (next_num, now, "Auto-created by sm run (pipeline-driven)"),
        )
        sprint_id = cursor.lastrowid
        conn.commit()
        print(f"  Sprint #{next_num} ({sprint_id}) — driven, active")
        print()

        # Construct config for state machine
        cfg = {}
        config_path = args.config or "config.json"
        if os.path.exists(config_path):
            with open(config_path) as f:
                cfg.update(json.load(f))

        if args.max_iterations is not None:
            cfg["max_iterations"] = args.max_iterations
        if args.max_retries is not None:
            cfg["max_retries"] = args.max_retries
        if args.resume:
            cfg["resume"] = True
        if args.target_feature_count:
            cfg["target_feature_count"] = args.target_feature_count

        cfg["db_path"] = db_path
        cfg["sprint_id"] = sprint_id
        cfg["sprint_number"] = next_num

        print("  Pipeline-driven: agents resolved per state from pipeline_states")
        print()

        from genesis_sm.state_machine import run_with_config
        run_with_config(cfg)

    finally:
        conn.close()
```

---

## Backward Compatibility

**Breaking change.** Any script or automation that calls `sm run --profile scribe-PLAN` will fail with an unrecognized argument error. These callers must be updated to call `sm run` without `--profile`.

This is acceptable because:
- The pipeline engine has resolved agents from `pipeline_states` since Sprint 03
- The `--profile` flag has been misleading since that time — it appears to work but is ignored after the first phase
- No production scripts depend on it (the Sprint 03-07 test suites never use `--profile`)

---

## Updates to `state_machine.py`

The module's `run_with_config()` function currently reads `cfg["profile"]` to set env vars and log the active profile. After the removal:

1. Remove the `cfg["profile"]` read at function entry
2. The pipeline engine (`pipeline/engine.py`) already reads agent names from `pipeline_states` and dispatches to the correct profile per state
3. `MATSYA_PROFILE` env var is no longer set at `run` time. If a phase script needs to know which agent it is, it reads the state name from the pipeline context

---

## Verification

```bash
# Test 1: sm run without --profile
sm run
# Expected: sprint auto-created, pipeline resolves agents from pipeline_states

# Test 2: --profile flag is gone
sm run --profile scribe-PLAN
# Expected: error — unrecognized argument

# Test 3: Help text
sm run --help
# Expected: no --profile listed

# Test 4: Full pipeline cycle
sm run --max-iterations 1
# Expected: engine steps through PLAN → WRITE → REVIEW → TEST_BUILD → TEST_RUN → SPRINT_GATE
# Each state dispatches to its correct agent from pipeline_states.agent_name
```

---

## Files to Change

| File | Change |
|------|--------|
| `src/genesis_sm/cli.py` line 1438–1439 | Remove `--profile` argument entirely. Update help text. |
| `src/genesis_sm/cli.py` `cmd_run()` | Remove profile-loading block, env var setting, `cfg["profile"]`. |
| `src/genesis_sm/state_machine.py` `run_with_config()` | Remove `cfg["profile"]` read. Pipeline engine handles agent resolution. |

---

*Written by Saraswati, from Kurma's signal. Built by Matsya. Watched by Kurma.*
