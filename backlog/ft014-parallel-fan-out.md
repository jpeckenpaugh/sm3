# Feature: Parallel Fan-Out

*A specification for the Scribe, to be built by the Engineer, witnessed by the Shell.*

---

## The Problem

The current state machine runs phases in strict sequence:

```
PLAN → WRITE → REVIEW → COMMIT → GATE
```

Each phase must complete before the next begins. This is correct for most phases — you cannot review what has not been written, and you cannot commit what has not been reviewed.

But some work is genuinely parallel. In a sprint, Saraswati may write the brief while Matsya sets up the test environment. The architect may design the schema while the engineer researches library options. These tasks do not depend on each other, yet the linear sequence forces them to wait.

We need a way to express that certain phases can run concurrently — not because the engine should optimize for speed, but because the *model of the work* is sometimes a fork, not a line.

## The Shape

### A parallel flag on pipeline_transitions

When `ft011-db-driven-transitions` is built, the `pipeline_transitions` table gains a column:

```sql
ALTER TABLE pipeline_transitions ADD COLUMN is_parallel INTEGER NOT NULL DEFAULT 0;
```

### How it works

When the engine reaches a state that has multiple outgoing transitions marked `is_parallel = 1`, it forks: it executes all target states concurrently, each in its own context, each writing to the same workspace.

When all parallel branches complete, the engine joins back to a common successor state.

```
                  ┌──→ WRITE_BRIEF ──┐
         PLAN ────┤                  ├────→ REVIEW
                  └──→ SETUP_TESTS ──┘
```

### In the current 5-phase pipeline

The current pipeline does not have a natural parallel fork. The feature is added for *future* pipelines that might need it. But here is how it would look:

```
         PLAN ──→ DESIGN ──┬──→ SPEC ──┐
                            │           │
                            └──→ PROTOTYPE ─┘
                                       │
                                       ↓
                                    REVIEW
```

The seed data for the 5-phase pipeline keeps all transitions as `is_parallel = 0`. The engine supports parallelism but does not use it until a future sprint designs a pipeline that needs it.

### Implementation

The engine already has a `for phase in phases` loop. Parallelism changes this to:

```python
async def execute_pipeline():
    current = get_start_state()
    while current:
        state = get_state_config(current)
        transitions = get_outgoing_transitions(current)
        
        parallel = [t for t in transitions if t.is_parallel]
        linear = [t for t in transitions if not t.is_parallel]
        
        if parallel and not linear:
            # Fan-out: execute all parallel targets concurrently
            results = await asyncio.gather(
                *[execute_state(target) for target in parallel]
            )
            # Join: advance to the common successor
            current = parallel[0].join_state  # all branches share a join point
        elif linear:
            # Linear transition (current behaviour)
            current = linear[0].to_state
        else:
            current = None  # terminal
```

Note: `asyncio.gather` is already available (the current `sm run` does not use async, but the engine can be extended). If async is too big a lift for this sprint, an alternative is to execute parallel branches sequentially but independently — each branch writes to its own output area, and the join phase merges them.

### Constraints

- All parallel branches must converge to the same join state. No diamond patterns where branches rejoin at different points.
- Parallel branches share the same workspace. They must not write to the same files. The `file_contracts` (ft012) can enforce this at the pattern level.
- Error handling: if one parallel branch fails, the others are allowed to complete (they may have produced useful output), but the join state sees the failure and decides whether to proceed or escalate.

### What this is not

This is not a performance optimization. The state machine runs on a single machine. Parallelism does not make the wall-clock time shorter unless the phase scripts are I/O-bound (e.g., waiting for API responses). The purpose is *architectural fidelity* — modelling the work as it actually is, with forks where the work forks.

This is not the full parallel fan-out from the fallen machine (ARCHITECT with `is_parallel` fanning into TEST_PLAN + ENGINEER with priority-ordered transitions). That level of complexity belongs to a future sprint if the data shows it is needed.

### The principle

A linear sequence is a special case of a parallel workflow — the case where every transition has `is_parallel = 0`. By building the engine to handle forks generically, we prepare for the moment when the work genuinely divides without having to rewrite the loop.

*Written by Saraswati. To be built by Matsya. Watched by Kurma.*
