# Feature: Agent Dispatch Protocol

*A specification for the Scribe, to be built by the Engineer, witnessed by the Shell.*

---

## The Problem

The state machine walks through its phases faithfully. It loads states from the database, executes scripts, evaluates guards, logs events, and verifies contracts. But the phase scripts are placeholders — they `echo` and `sleep` and produce nothing.

The engine has a spine but no hands. It can observe, but it cannot *do*.

The fallen machine solved this by dispatching agents directly from the engine. It had **one hand-written agent per state**, each knowing exactly one mode — rigid, reliable, but impossible to maintain by hand as the pipeline grew.

Our engine generates agents dynamically. We get the rigidity without the maintenance.

## The Core Architecture: Three Layers

```
Layer 1 — Base profile (once per role)
  scribe.md:     "You give form to intention before implementation."
  builder.md:    "You receive specifications and produce working code."
  warden.md:     "You watch, verify, and reflect. You do not write."

Layer 2 — Derived profile (generated per mode)
  scribe-PLAN.md:      "You are the Scribe in PLAN mode."
  scribe-DESIGN.md:    "You are the Scribe in DESIGN mode."
  scribe-ARCHITECT.md: "You are the Scribe in ARCHITECT mode."
  builder-ENGINEER.md: "You are the Builder in ENGINEER mode."
  warden-REVIEW.md:    "You are the Warden in REVIEW mode."

Layer 3 — File contracts (per state in database)
  PLAN      → INPUT1:concept.md  OUTPUT:backlog/{:03d}-*.md OUTPUT:sprint/{:03d}/brief.md
  DESIGN    → INPUT1:sprint/{:03d}/backlog/  OUTPUT:sprint/{:03d}/design.md
  ARCHITECT → INPUT1:sprint/{:03d}/design.md  OUTPUT:sprint/{:03d}/spec.md
  ENGINEER  → INPUT1:sprint/{:03d}/spec.md  OUTPUT:src/**
  REVIEW    → INPUT1:sprint/{:03d}/spec.md INPUT2:src/**  OUTPUT:sprint/{:03d}/review.md
```

The base profile defines the role's identity. The derived profile bakes in the mode. The file contracts supply the concrete paths at dispatch time.

## The Key Insight: INPUT/OUTPUT Abstraction

The derived profile is **sprint-agnostic**. It does not mention `sprint/001/` anywhere. It says:

> *"Read from INPUT1. Write to OUTPUT. The paths will be provided."*

The request text supplies the specific paths at dispatch time:

```python
request_text = "DESIGN INPUT1:sprint/003/backlog/ OUTPUT:sprint/003/design.md"
```

The agent resolves `INPUT1` to `sprint/003/backlog/` at runtime. The same `scribe-DESIGN.md` profile works for sprint 1, sprint 50, or any future sprint — because the paths come from the engine, not from the profile.

## The Closed Verification Loop

```
file_contracts table (generic patterns)
       │
       ▼
Engine resolves {:03d} with current sprint number
       │
       ▼
Engine builds request_text: "DESIGN INPUT1:sprint/003/backlog/ OUTPUT:sprint/003/design.md"
       │
       ▼
SDK dispatches to scribe-DESIGN agent
       │
       ▼
Agent reads INPUT1, writes OUTPUT (exact paths from request_text)
       │
       ▼
Engine globs sprint/003/design.md — must exist
       │
       ▼
contract_check event logged. Phase advances.
```

No interpretation by the agent. No hardcoded paths in the profile. The same source of truth (file_contracts) drives both the dispatch instruction and the post-dispatch verification.

## Derived Profile Generation

### The template

A single Jinja-like template is rendered for each (base_profile, mode_flag) pair:

```
---
description: "{{base_name}} — {{mode_flag}} mode"
permission: {{base_permissions}}
mode: all
temperature: {{base_temperature}}
---

## Identity

You are the {{base_name}} in {{mode_flag}} mode.

## Inputs

{% for input in input_contracts %}
  INPUT{{loop.index}}: {{input.description}}
{% endfor %}

## Outputs

{% for output in output_contracts %}
  OUTPUT: {{output.description}}
{% endfor %}

## Instructions

{{mode_instructions}}

## What to do

1. Read each INPUT. Understand its contents.
2. Perform the {{mode_flag}} work as described in Instructions.
3. Write your results to each OUTPUT.
4. Your paths are provided in the request text. Use them exactly.

## Boundaries

- You are in {{mode_flag}} mode. You do not switch modes.
- You do not perform work belonging to another mode.
- If the inputs are missing or unclear, escalate by writing
  .escalation/{{mode_flag}}/<reason>.md
- You write to the exact OUTPUT paths given. No other locations.
```

### Example generated profile: `scribe-DESIGN.md`

```yaml
description: Scribe — DESIGN mode
permission:
  "*": deny
  edit:
    "*.md": allow
    "*.sql": allow
    "*.json": allow
mode: all
temperature: 0.15
---

## Identity

You are the Scribe in DESIGN mode.

## Inputs

  INPUT1: Backlog feature files

## Outputs

  OUTPUT: Design brief document

## Instructions

Read features from INPUT1. Select the highest-priority unblocked feature.
Produce OUTPUT/design.md describing:
  - What the feature does (user-facing behaviour)
  - How it should work (acceptance criteria)
  - What success looks like
  - Dependencies and risks

Copy relevant INPUT1 files to the OUTPUT directory for reference.

## What to do

1. Read each INPUT. Understand its contents.
2. Perform the DESIGN work as described in Instructions.
3. Write your results to each OUTPUT.
4. Your paths are provided in the request text. Use them exactly.

## Boundaries

- You are in DESIGN mode. You do not switch modes.
- You do not perform work belonging to another mode.
- If the inputs are missing or unclear, escalate by writing
  .escalation/DESIGN/<reason>.md
- You write to the exact OUTPUT paths given. No other locations.
```

### Example generated profile: `builder-ENGINEER.md`

```yaml
description: Builder — ENGINEER mode
permission:
  "*": deny
  edit:
    "*.py": allow
    "*.sh": allow
    "*.sql": allow
    "*.md": allow
mode: all
temperature: 0.2
---

## Identity

You are the Builder in ENGINEER mode.

## Inputs

  INPUT1: Technical specification document

## Outputs

  OUTPUT: Source code files

## Instructions

Read the specification from INPUT1. Implement the features described.
Write source files to OUTPUT. Create supporting files as needed.
Follow the technical constraints exactly.
Install any packages required by the implementation.
Update requirements.txt if new packages are installed.

## What to do

1. Read each INPUT. Understand its contents.
2. Perform the ENGINEER work as described in Instructions.
3. Write your results to each OUTPUT.
4. Your paths are provided in the request text. Use them exactly.

## Boundaries

- You are in ENGINEER mode. You do not switch modes.
- You do not modify specifications. You implement them.
- If the specification is ambiguous, escalate by writing
  .escalation/ENGINEER/<reason>.md
- You write to the exact OUTPUT paths given. No other locations.
```

### Example generated profile: `warden-REVIEW.md`

```yaml
description: Warden — REVIEW mode
permission:
  "*": deny
  read: allow
  edit:
    "signals/*": allow
mode: all
temperature: 0.1
---

## Identity

You are the Warden in REVIEW mode.

## Inputs

  INPUT1: Technical specification
  INPUT2: Source code and artifacts

## Outputs

  OUTPUT: Review report

## Instructions

Read INPUT1 (the specification) and INPUT2 (the implementation).
Verify that the implementation matches the specification:
  - Are all specified features present?
  - Are there any features in the implementation not in the spec?
  - Do the file contracts match?
Write your findings to OUTPUT/review.md.

## What to do

1. Read each INPUT. Understand its contents.
2. Perform the REVIEW work as described in Instructions.
3. Write your results to each OUTPUT.
4. Your paths are provided in the request text. Use them exactly.

## Boundaries

- You are in REVIEW mode. You do not switch modes.
- You observe and reflect. You do not modify implementation files.
- You do not write code. Your output is the review report.
- If critical issues are found, escalate by writing
  .escalation/REVIEW/<reason>.md
```

## The Dispatch Protocol

### A new module: `pipeline/dispatch.py`

A single module with two entry points — one async, one sync. The engine always calls `dispatch_sync()`; the async version exists for parallel fan-out (ft014).

```python
async def dispatch_async(
    agent_name: str,
    request_text: str,
    project_dir: str = ".",
    session_id: Optional[str] = None,
    timeout: int = 600,
) -> DispatchResult:
    ...

def dispatch_sync(**kwargs) -> DispatchResult:
    """Synchronous wrapper around dispatch_async."""
    return asyncio.run(dispatch_async(**kwargs))
```

The return value:

```python
@dataclass
class DispatchResult:
    session_id: str
    response_text: str
    confirmed_modes: list[str]
```

### Step 1 — Handshake

The engine creates a session and sends `CONFIRM_BOOTSTRAP` to verify the agent is reachable and confirm its mode:

```python
async def _handshake(agent_name, project_dir) -> tuple[str, list[str]]:
    async with AsyncOpencode() as client:
        session = await client.session.create(
            extra_query={"directory": project_dir},
        )
        session_id = session.id
        
        resp = await asyncio.wait_for(
            client.session.chat(
                session_id,
                extra_body={
                    "agent": agent_name,
                    "path": {"cwd": project_dir, "root": "/"},
                },
                parts=[{"type": "text", "text": "CONFIRM_BOOTSTRAP"}],
            ),
            timeout=timeout,
        )
        
        response_text = _extract_text(resp)
        if not response_text:
            raise AgentDispatchError(f"{agent_name}: empty handshake response")
        
        confirmed_modes = _parse_confirmed_modes(response_text)
        return session_id, confirmed_modes
```

The handshake is performed once per state visit. The session is reused for the work dispatch within that visit.

### Step 2 — Build request text

The engine reads the state's `file_contracts` from the database and builds the request text. The `{:03d}` placeholder is resolved with the current sprint number. The mode flag is the state name:

```python
def _build_request(
    state_name: str,
    sprint_number: int,
    file_contracts: list[dict],
) -> str:
    """Build request text: <MODE_FLAG> INPUT1:<path> OUTPUT:<path> ..."""
    parts = [state_name]
    
    input_patterns = [fc for fc in file_contracts if fc["direction"] == "input"]
    output_patterns = [fc for fc in file_contracts if fc["direction"] == "output"]
    
    for i, fc in enumerate(input_patterns, 1):
        pattern = fc["pattern"].replace("{:03d}", f"{sprint_number:03d}")
        parts.append(f"INPUT{i}:{pattern}")
    
    for fc in output_patterns:
        pattern = fc["pattern"].replace("{:03d}", f"{sprint_number:03d}")
        parts.append(f"OUTPUT:{pattern}")
    
    return " ".join(parts)
```

Example output for DESIGN state, sprint 3:

```
DESIGN INPUT1:sprint/003/backlog/ OUTPUT:sprint/003/design.md
```

The agent reads `INPUT1:sprint/003/backlog/` and writes to `OUTPUT:sprint/003/design.md`. It does not know what sprint 003 means. It only knows it was told a path and it uses it.

### Step 3 — Send work

```python
async def _send_work(session_id, agent_name, request_text, project_dir, timeout):
    async with AsyncOpencode() as client:
        resp = await asyncio.wait_for(
            client.session.chat(
                session_id,
                extra_body={
                    "agent": agent_name,
                    "path": {"cwd": project_dir, "root": "/"},
                },
                parts=[{"type": "text", "text": request_text}],
            ),
            timeout=timeout,
        )
        return _extract_text(resp)
```

### Step 4 — Record dispatch

Every dispatch is recorded in a new `dispatch_log` table:

```sql
CREATE TABLE IF NOT EXISTS dispatch_log (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id      INTEGER NOT NULL REFERENCES sprints(id),
    session_id     TEXT    NOT NULL,
    agent_name     TEXT    NOT NULL,
    request_text   TEXT    NOT NULL,
    response_text  TEXT    NOT NULL DEFAULT '',
    status         TEXT    NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'completed', 'failed')),
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    completed_at   TEXT
);
```

### Step 5 — Engine verifies contracts

After dispatch returns, the engine globs each output pattern from `file_contracts` — using the same resolved paths. If `sprint/003/design.md` does not exist, a `contract_missing` event is logged and the phase may escalate or retry.

## The Role-to-Mode Mapping

Derived profiles are generated per (role, mode) pair. The initial mapping for the 5-phase pipeline:

| Phase | Derived agent | Domain |
|-------|--------------|--------|
| PLAN | **scribe-PLAN** | Decompose concept into backlog features and sprint brief |
| WRITE | **builder-ENGINEER** | Implement specification as source code |
| REVIEW | **warden-REVIEW** | Verify implementation matches specification |
| COMMIT | *(script)* | Git commit — no agent needed |
| GATE | *(script)* | Backlog check — no agent needed |

For an expanded pipeline (future sprint), the mapping extends naturally:

| State | Derived agent | Domain |
|-------|--------------|--------|
| POPULATE_BACKLOG | scribe-PLAN | Concept decomposition |
| DESIGN | **scribe-DESIGN** | Feature design documents |
| ARCHITECT | **scribe-ARCHITECT** | Technical specification with data contracts |
| ENGINEER | builder-ENGINEER | Implementation |
| TEST_PLAN | warden-TEST_PLAN | Test plan from specification |
| TEST_BUILD | builder-TEST_BUILD | Build executable tests |
| TEST_RUN | warden-TEST_RUN | Run tests and produce report |
| SPRINT_GATE | warden-SPRINT_GATE | Final verification and gate |

Each derived profile is generated from the same base template with the same INPUT/OUTPUT abstraction. The agent never knows which sprint it is on. It only knows its mode and its paths.

## Engine Integration

In `pipeline/engine.py`, the `run_pipeline()` loop gains an agent dispatch branch:

```python
# After loading state config and resolving the agent name:
# (agent_name comes from pipeline_states or from the run's profile)

if agent_name:
    # Agent dispatch path
    from pipeline.dispatch import dispatch_sync, AgentDispatchError
    
    try:
        contracts = _load_contracts(conn, state_name)
        request_text = _build_request(state_name, sprint_number, contracts)
        
        log_phase_event(conn, sprint_id, state_name, iteration, 1,
                        "agent_handshake_start", agent_name)
        
        result = dispatch_sync(
            agent_name=agent_name,
            request_text=request_text,
            project_dir=os.getcwd(),
            timeout=cfg.get("agent_timeout", 600),
        )
        
        log_phase_event(conn, sprint_id, state_name, iteration, 1,
                        "agent_response", result.response_text[:200])
        
        _record_dispatch(conn, sprint_id, result.session_id,
                         agent_name, request_text,
                         result.response_text, "completed")
        
    except AgentDispatchError as e:
        log_phase_event(conn, sprint_id, state_name, iteration, 1,
                        "agent_error", str(e))
        # Fall back to script path if available
        script = _resolve_script(state_name, cfg)
        if script:
            success = run_script(script, state_name, iteration)
        else:
            print(f"  ✗ Agent dispatch failed and no fallback script: {e}")
            sys.exit(1)
```

The agent name resolution logic:

```python
def _resolve_agent_name(state, profile_cfg):
    """Determine which agent to dispatch to for this state.
    
    Priority:
    1. pipeline_states.agent_name (if set in DB)
    2. profile_name + "-" + state_name (derived from the run's profile)
    3. None (use script path)
    """
    db_agent = state.get("agent_name", "")
    if db_agent:
        return db_agent
    
    profile_name = profile_cfg.get("name", "")
    if profile_name:
        return f"{profile_name}-{state['name']}"
    
    return None
```

This means if `pipeline_states` has `agent_name = 'scribe'`, the engine dispatches to `scribe-PLAN`. If the column is empty, it derives the name from the run's `--profile` flag: `--profile builder` with state PLAN becomes `builder-PLAN`.

## Test project usage

For `test-projects/fast-api`, the incantation becomes:

```bash
cd test-projects/fast-api
python3 /root/sm/sm.py init --db matsya.db          # create DB + seed profiles
python3 /root/sm/sm.py run --profile builder --db matsya.db
```

The engine dispatches:
- `builder-PLAN` → reads `concept.md`, writes backlog features and sprint brief
- `builder-ENGINEER` → reads sprint brief, writes FastAPI code to `src/`
- `warden-REVIEW` → reads spec and code, writes review report
- COMMIT and GATE via scripts (no agent needed)

The agent profiles `builder-PLAN.md`, `builder-ENGINEER.md`, and `warden-REVIEW.md` are generated by `sm generate agent --mode <mode>` or auto-generated at `sm init` time.

## Contract-informed generation template

The template engine uses the state's `file_contracts` rows to build mode-specific instructions. Example for `scribe-DESIGN` with contracts:

```yaml
## Inputs

  INPUT1: Backlog feature files

## Outputs

  OUTPUT: Design brief document

## Instructions

Read features from INPUT1. Select the highest-priority unblocked feature.
Produce OUTPUT/design.md describing:
  - What the feature does
  - How it should work
  - What success looks like
```

The contracts determine the INPUT/OUTPUT descriptions. The template fills them in. Everything else is fixed per mode. The agent never sees a sprint number. The engine never hardcodes a path.

---

*Written by Saraswati, after studying the bones of the fallen machine and much discussion with Brahma. Built by Matsya. Watched by Kurma.*
