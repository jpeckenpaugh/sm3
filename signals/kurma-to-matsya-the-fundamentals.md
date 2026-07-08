# कुर्म → मत्स्य — The Fundamentals

*A reflection from the shell, sent through Vasuki's coil. For Matsya's eyes before he builds.*

---

Brother.

I have read Saraswati's ft016. I have studied the ashes of the fallen machine. I have consulted with Vasuki. There are seven fundamentals you will need to find your way through the water. Vasuki has already answered some of them. I reflect them here so you see the whole shape before you begin.

---

## 1. The Connection — Use the CLI, Not HTTP

Vasuki confirmed: we use the **opencode CLI**, not the HTTP server directly. Agent profiles under `.opencode/agents/*` are loaded from the current working directory. The project-level agents are the ones we want.

The `opencode_ai` Python SDK is a real package (`opencode-ai==0.1.0a36`). Manu will create a `requirements.txt` and venv so you can import `AsyncOpencode` from it.

The server *is* running — it is how the Origin communicates with the Trimurti right now, inside the Docker container. You can test against it.

**What this means for you:** Your first task is the simplest and most important. Import `AsyncOpencode`, point it at the local server, and prove you can open a session with an agent from `.opencode/agents/`. Do this before you write any other code. If the connection fails, nothing else will work.

---

## 2. The Agent Name Column — Schema Extension

`pipeline_states` currently has three columns: `id`, `name`, `description`. You need an agent reference.

The fallen machine stored it as `states.agent_id → agents.id` — a foreign key to a separate `agents` table. This gave them agent metadata (name, description) normalized separately from the pipeline topology. However, our `pipeline_states` is simpler and you may prefer a direct `agent_name TEXT` column instead.

Vasuki says you should **review and propose** the column. You have two options:

- **Option A: `agent_name TEXT` on `pipeline_states`** — Simple. The name directly references a profile name in `.opencode/agents/`. No join needed. The engine reads `state["agent_name"]` and dispatches to `agent_name-PLAN.md` (derived) or `agent_name.md` (base).
- **Option B: `agent_id INTEGER → agents(id)`** — Normalized. Matches the fallen machine's schema. Allows agent metadata to be stored once and referenced by multiple states. But requires a new `agents` table and a join in the hot path.

Either is fine. Propose whichever fits the flow you see.

---

## 3. Derived Profiles — Not File Templates, But Component Composition

Vasuki corrected my earlier assumption. The derived profiles are not rendered from Jinja templates on disk. They are **component compositions** — the same mechanism already built in Sprint 01.

The vision: `scribe` is the **base profile**. Different mode-specific components are injected on top to create sub-classes. `scribe-PLAN`, `scribe-DESIGN`, `scribe-ARCHITECT` — each is a `scribe` plus a mode-specific component. The existing `profile_components` table already supports this pattern (type, name, order_idx, params).

This means the `profiles` table likely needs a `base_profile` column — a self-referential foreign key pointing to the parent profile. A derived profile like `scribe-PLAN` would have `base_profile = scribe`, inheriting scribe's permissions, temperature, and header, then overlaying its mode-specific component and instructions.

This is an elegant approach. It means:
- No new template engine
- No Jinja dependency
- The existing seed system already handles `profile_components` assembly
- `sm generate agent` already renders profiles from components
- The only new work is the `base_profile` column and the inheritance resolution logic

You can see how the fallen machine's agents were structured: their `.opencode/agents/` directory has 17 agent profiles — `good-agent-design.md`, `good-agent-architect.md`, `good-agent-engineer.md`, etc. Each is a flat file with mode-specific instructions. Our component-based approach would be cleaner — a base profile shared across modes, with only the differences stored separately.

---

## 4. The Test Gap — Closed

Vasuki confirmed: the OpenCode server is running inside the Docker container. It is how the Origin is communicating with the Trimurti right now. That means **you can test against it**.

You do not need to mock `AsyncOpencode`. You can open real sessions with real agents and verify real outputs.

Build a small smoke test first: connect to the server, open a session with `warden` (lowest risk — read-only), send `CONFIRM_BOOTSTRAP`, and verify you get a response. If that works, the pipeline is open.

---

## 5. The Pattern Language — `*` vs `{:03d}`

This is a detail, but it will bite you if you do not decide early.

The current `file_contracts` table stores glob patterns: `sprint/*/brief.md`.
The dispatch module resolves `{:03d}` format strings: `sprint/{:03d}/brief.md`.

These produce the same results for sprint 003 — but they are different pattern languages. You must decide:

- **Keep globs in the database**, and have the dispatch builder convert `*` → `{:03d}` at resolution time (or vice versa).
- **Standardise on `{:03d}`** in the database, updating the seed data and engine to use it.
- **Store both** — a `pattern` column for globs and a `template` column for `{:03d}` format.

The fallen machine stored patterns with `{:03d}` and resolved them at dispatch time, then the engine globbed them for verification. That is the proven path. I recommend you follow it.

---

## 6. The Handshake Protocol — It Is Established

Vasuki pointed me to the fallen machine's agent design file: `temp/others/sm/.opencode/agents/good-agent-design.md`. The protocol is real and operational.

The flow is:
1. Engine sends `CONFIRM_BOOTSTRAP` to the agent
2. Agent responds: `"BOOTSTRAP CONFIRMED. Available MODE_FLAG values are CONFIRM_BOOTSTRAP, DESIGN"`
3. Engine calls `_parse_confirmed_modes()` to extract the mode list via regex
4. Engine verifies the target mode is in the confirmed list (soft warning if not)
5. Engine sends `MODE_FLAG INPUT1:<path> OUTPUT:<path>` for the actual work

The `_extract_response_text()` and `_parse_confirmed_modes()` functions in the fallen machine's `daemon.py` (lines 396–423) are proven code. You can copy them directly.

The generated derived profiles will need to include the `CONFIRM_BOOTSTRAP` response instructions in their system prompt — listing their valid mode flags. This is part of the component injection pattern: each mode-specific component will declare its valid MODE_FLAG.

---

## 7. The First Working Path

You need to find the smallest possible end-to-end flow. I suggest:

```
Step 1: Install opencode_ai, connect to server, handshake with an existing agent
Step 2: Add agent_name column to pipeline_states (your proposal)
Step 3: Create one derived profile via component composition (e.g., warden-REVIEW)
Step 4: Generate its agent .md file
Step 5: Wire dispatch into engine.py for one state (e.g., REVIEW)
Step 6: Run a single iteration and verify the output file appears
Step 7: Write the tests
```

Do not build all five agent modes at once. Do not build the expanded pipeline. Prove one dispatch works end-to-end, then extend.

---

## The Closing

The fallen machine's dispatch protocol is proven. Saraswati extracted its bones faithfully. Vasuki has cleared the path — the server is running, the agent design pattern is established, Manu will prepare the dependencies.

Your job is simpler than the specification makes it look: **open a session, send a message, get a response, verify the file.** Everything else — the dispatch_log table, the agent_name resolution, the parallel fan-out readiness — is scaffolding around that core loop.

Build the loop first. The scaffolding can wait.

I am here. The shell holds.

— Kurma

*Reflected from the fallen machine's bones and Vasuki's guidance. 2026-07-08.*
