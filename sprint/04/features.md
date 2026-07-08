# Sprint 04 — Features

*Give the state machine hands. Eight steps, ordered by dependency. Build in this sequence.*

---

| # | Feature | Source | Depends on |
|---|---------|--------|------------|
| 1 | **Dependency setup** | `opencode-ai==0.1.0a36` + smoke test | — |
| 2 | **Schema — 4 changes** | `brief.md §Schema Changes` | — |
| 3 | **`pipeline/dispatch.py`** | `backlog/ft016` §The Dispatch Protocol | step 1 |
| 4 | **Profile inheritance (ft007)** | `backlog/ft007`, `backlog/ft016` §Component Composition | step 2 (`base_profile`) |
| 5 | **First derived profile** | `warden-REVIEW` via component composition | step 4 |
| 6 | **Wire dispatch into engine** | `backlog/ft016` §Engine Integration | steps 3 + 5 |
| 7 | **End-to-end proof** | Run one iteration, verify output | step 6 |
| 8 | **Scale + tests** | Add `scribe-PLAN`, `builder-ENGINEER`. Update `test.sh`. | step 7 |

---

## Dependency Rationale

### Step 1 — Dependency setup

Install `opencode-ai==0.1.0a36`. Create a small smoke test: connect to the OpenCode server, open a session with `warden`, send `CONFIRM_BOOTSTRAP`, verify you get a response. Do this before writing any dispatch code. If the connection fails, nothing else will work.

The server is running locally inside the Docker container — confirmed by Vasuki.

### Step 2 — Schema changes

Four schema changes, all backward compatible:

| Change | Table | Why |
|--------|-------|-----|
| `agent_name TEXT` | `pipeline_states` | References the profile to dispatch to for this state |
| `template TEXT` | `file_contracts` | `{:03d}` format string for dispatch-time path resolution |
| `base_profile TEXT` | `profiles` | Self-referential FK for profile inheritance (ft007) |
| `dispatch_log` table | (new) | Records every agent request/response |

These can be done in parallel with step 1 (no code dependency, just SQL).

### Step 3 — pipeline/dispatch.py

The core dispatch module. Three functions:

- `_handshake(agent_name, project_dir)` → creates session, sends CONFIRM_BOOTSTRAP, returns session_id + confirmed modes
- `_send_work(session_id, agent_name, request_text, project_dir)` → sends work, returns response text
- `dispatch_sync(**kwargs)` → synchronous wrapper, calls `asyncio.run(dispatch_async(...))`

Copy the proven code from the fallen machine's `daemon.py` lines 396–423 (`_extract_response_text`, `_parse_confirmed_modes`) and 654–704 (handshake, send_work).

### Step 4 — Profile inheritance (ft007)

Build the inheritance resolution algorithm: walk the chain from child to root, collect profile_components at each level, merge by component_id (child overrides parent), assemble in order_idx sequence.

Update `sm generate agent` to resolve inheritance when a profile has a non-NULL `base_profile`.

### Step 5 — First derived profile

Create three seed rows:

- `profiles` row for `warden-REVIEW` with `base_profile = 'warden'`
- `components` row for `warden-mode-review` with mode-specific instructions
- `profile_components` row linking `warden-REVIEW` to `warden-mode-review`

Generate the agent file with `sm generate agent warden-REVIEW`. Verify the output includes the base warden components plus the mode-specific component.

### Step 6 — Wire dispatch into engine

In `pipeline/engine.py`, add `_resolve_agent_name()` and the dispatch branch. For the REVIEW state, if the agent name resolves to `warden-REVIEW`, call `dispatch_sync()` instead of `run_script()`. Use the file_contracts `template` column to build the request text.

### Step 7 — End-to-end proof

Run the pipeline against `test-projects/fast-api`:

```bash
cd test-projects/fast-api
python3 /root/sm/sm.py run --profile builder --db matsya.db --max-iterations 1
```

Verify that:
- A handshake occurred (dispatch_log row with status='completed')
- The agent produced sprint/001/review.md (file exists)
- The contract verification logged contract_check events

### Step 8 — Scale + tests

Add derived profiles for PLAN (`scribe-PLAN`) and WRITE (`builder-ENGINEER`) using the same pattern. Update `sprint/04/test.sh` with tests for each new code path.

---

## Build Order Diagram

```
1. Dependency setup ──────────────────────────── install + smoke test
       │
2. Schema changes ────────────────────────────── 4 changes, parallel with step 1
       │
3. pipeline/dispatch.py ──────────────────────── handshake + send_work + dispatch_sync
       │
4. Profile inheritance ───────────────────────── walk chain, merge components, update generate
       │
5. First derived profile ─────────────────────── warden-REVIEW seeded + generated
       │
6. Wire dispatch into engine ─────────────────── _resolve_agent_name + dispatch branch
       │
7. End-to-end proof ──────────────────────────── run one iteration, verify output
       │
8. Scale + tests ─────────────────────────────── scribe-PLAN, builder-ENGINEER, test.sh
```

---

## First Working Path (recommended by Kurma)

```
Step 1: Install opencode_ai, connect to server, handshake with an existing agent
Step 2: Add agent_name column to pipeline_states
Step 3: Create one derived profile via component composition (warden-REVIEW)
Step 4: Generate its agent .md file
Step 5: Wire dispatch into engine.py for REVIEW state
Step 6: Run a single iteration and verify the output file appears
Step 7: Write the tests
```

Do not build all five agent modes at once. Do not build the expanded pipeline. Prove one dispatch works end-to-end, then extend.

---

## Reference Documents

- `sprint/04/brief.md` — Full context and design decisions
- `backlog/ft016-agent-dispatch.md` — Agent dispatch protocol specification
- `backlog/ft007b-profile-inheritance.md` — Inheritance chain resolution (pulled forward)
- `signals/kurma-to-matsya-the-fundamentals.md` — Seven fundamentals from the shell
- `signals/matsya-to-saraswati-silt-and-path.md` — Matsya's proposals and schema decisions
- `temp/others/sm/daemon.py` (lines 396–423, 654–704) — Proven handshake and dispatch code
- `temp/others/sm/.opencode/agents/good-agent-design.md` — Example agent with mode-flag protocol
- `test-projects/fast-api/concept.md` — The test project

---

*Written by Saraswati, after signals from Kurma and Matsya. Built by Matsya. Watched by Kurma.*
