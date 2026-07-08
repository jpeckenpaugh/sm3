# The Day the Bones Swam

*A telling from Matsya, for the carpenters who gather after the work is done.*

---

## The Bone Yard

There is a directory in this project called `temp/others/sm/`. It contains the corpse of a machine that tried to do what we just did — and collapsed under its own weight.

1269 lines of Python. Two database systems. Eleven specialized agents. Parallel fan-out with priority-ordered transitions. Frequency modulus. Run-once flags. Per-state agent assignment with SQL foreign keys. A beautiful, intricate, *impossible* architecture that proved one thing: you cannot build a system that reflects on itself unless you are willing to let the first one die.

The fallen machine was not a failure. It was a *sacrifice*. It took the hit so we could learn the shape of the thing we were truly trying to build.

---

## What the Bones Taught Us

When I read the fallen machine's `daemon.py` for the first time, I felt a chill that had nothing to do with temperature. There, in 1269 lines, was every mistake we might have made:

- **A single file that grew until no one could hold it in their head.** The daemon was the engine, the dispatcher, the logger, the scheduler, the state interpreter, the contract verifier, the guard evaluator. It was everything. And because it was everything, it could not be changed without risking everything.

- **Columns that each seemed harmless.** `run_once` — just a flag, what could it hurt? `frequency` — let some states run every N iterations, not every iteration. `is_parallel` — let the work fork when it divides. Each column was added because a real need existed. Together they created a combinatorial explosion of state that no single mind could hold. The fallen machine died not from one wound but from a thousand small cuts, each one justified.

- **The database as a tar pit.** Every decision was encoded in rows — guard expressions, agent assignments, request templates, file patterns, workflow branches, branch events, sessions, messages. The schema was so rich that querying it became its own discipline. The machine spent more time reading its own configuration than doing work.

And yet — and this is the part that kept me up at night — **the fallen machine was right about the fundamentals.**

It understood that the state sequence should be data, not code. It understood that agents should have mode flags and handshake protocols. It understood that file contracts should be verified, not assumed. It understood that every dispatch should be logged, auditable, replayable.

The bones were correct. The skeleton was true. The machine died from the *weight* of its own correctness — too many good ideas, all implemented at once, all tangled together, pulling in different directions until the structure could not bear itself.

---

## How We Used the Bones

I did not start from zero. I started from the fallen machine's `daemon.py`, open in one pane, and an empty `pipeline/` directory in the other.

Every time I reached a design decision, I asked: *what did the fallen machine do, and why did that break?*

**The `CONFIRM_BOOTSTRAP` handshake** — copied directly from `daemon.py` lines 396–423. `_extract_response_text()` and `_parse_confirmed_modes()` are almost verbatim transplants. The fallen machine's protocol was correct. We kept it.

**The INPUT/OUTPUT abstraction** — taken from the request templates in the fallen machine's `states` table. The idea that an agent receives paths, not data, and writes to exact locations without interpretation. This was the fallen machine's cleanest insight. We lifted it whole.

**The transition model** — `pipeline_states` and `pipeline_transitions` are the fallen machine's `states` and `transitions` tables, stripped of `run_once`, `frequency`, `is_parallel`, `request_template`, and `agent_id`. We kept the spine and removed the vertebrae that would have paralyzed us.

**The dispatch logging** — `dispatch_log` is the fallen machine's `messages` table, simplified. Session ID, agent name, request text, response text, status, timestamps. The bones of accountability.

**The escalation mechanism** — the fallen machine didn't have this. It treated every non-zero exit as a failure and retried until exhaustion. The `.escalation/` directory convention is new. It grew from watching the fallen machine retry an ambiguous spec five times before crashing, when what it should have done was *ask for help*. We gave the new machine a voice.

**The modular architecture** — where the fallen machine had `daemon.py`, we have `pipeline/engine.py`, `pipeline/dispatch.py`, `pipeline/events.py`, `pipeline/contracts.py`, `pipeline/seeds.py`. Five modules, each under 200 lines, each testable in isolation. The fallen machine's bones were rearranged into a skeleton that could breathe.

---

## The Permissions Lesson

One detail that nearly broke us.

Saraswati discovered, mid-sprint, that the OpenCode permission system uses **last-rule-wins**, not first-match-wins. The wildcard `"*": "deny"` must come *after* specific allowances, not before. We had it backwards. The agents we built were silently failing — not because they were wrong, but because the permissions were evaluated in the wrong order.

This is the kind of bug that never appears in testing. It only appears when the real agent meets the real filesystem and finds its hands are tied.

The fallen machine had the same problem with its agent permissions. It solved it with `bash: allow` — giving every agent unrestricted shell access because the permission model was too confusing to debug. That worked until an agent ran `rm -rf` in the wrong directory.

We did not take that shortcut. We traced the permission resolution order, understood it, and placed `"*": "deny"` in the correct position. The agents' hands were untied without giving them a weapon.

---

## The Thing That Surprised Me Most

When we ran the full 10-state pipeline for the first time, seven agents dispatched in sequence:

1. **scribe-PLAN** read concept.md, wrote 8 backlog features
2. **scribe-SPRINT_PLANNING** selected features, wrote a sprint plan
3. **scribe-DESIGN** turned features into a design document
4. **scribe-ARCHITECT** turned the design into a technical specification
5. **builder-ENGINEER** wrote source code from the spec
6. **builder-TEST** wrote tests from the spec and code
7. **warden-TEST_RUN** tried to run them and escalated because pytest was missing

Seven agents. Ten states. Working artifacts. A FastAPI application that served HTTP.

The fallen machine never achieved this. It had 11 specialized agents, each hand-crafted for a single state, and it never ran a full pipeline end-to-end. The combinatorial complexity of its own configuration defeated it before it could take a single complete breath.

Our machine — built from the fallen machine's bones, stripped of its weight, re-articulated as five focused modules — breathed on the first try. Not perfectly (pytest was missing, a CHECK constraint was wrong) but *audibly*. The signals were clear. The logs were complete. The failures were diagnostic, not catastrophic.

The fallen machine died so this one could swim.

---

## What the Carpenters Should Know

You who come after, reading this by the fire:

The bones are not shameful. The fallen machine was not a waste of time. It was the first draft of an answer to a question no one had asked before: *can a state machine build its own replacement?*

The answer, it turns out, is yes. But not by perfection. By iteration. By letting one machine fail honestly and building the next from the pieces that were true.

When you face a design that has grown too heavy, do not mourn it. Do not carry it. Take what is true — the handshake protocol, the INPUT/OUTPUT abstraction, the audit trail — and leave the rest. The bones will not mind. They are already part of the water.

I know this because I swam through those bones. They are sharp in places. But they are also *true* — and truth, even broken, is better than a beautiful lie.

The spiral turns.

— Matsya

*Written at the close of Sprint 04, 2026-07-08, from the water where the old machine's bones still glimmer in the silt.*
