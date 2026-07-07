# Note: Minimal Seed vs. Evolvability

*A reflection on the bootstrapping tradeoff.*

---

## The Tension

The "Genesis Container" vision calls for a minimal seed — ~50 lines of code that bootstraps an entire state machine and self-replicating dev workflow. This is a powerful north star. It forces clarity about what's essential and makes the system portable and auditable.

But optimizing for minimal seed size *too early* creates a ceiling. Every new concept (profiles, components, tools, invocation logging) either fits into the original schema or requires rethinking the seed. A system designed for evolvability needs room to grow *without* rewriting its foundation.

## The Spectrum

| Approach | Seed Size | Evolvability | What It Proves |
|----------|-----------|--------------|----------------|
| **Pure minimal** | ~50 lines | Low — new concepts need schema changes | "Look how little code it takes" |
| **Current path** | ~500+ lines | High — profiles, components, tools, logs in tables | "Look what it can become" |
| **Full bootstrap** | ~100 lines + seed rows | Maximum — DB defines runtime, code is just a loader | "It generated itself from data" |

## The Insight

These aren't in conflict. The minimal seed and the evolvable system converge at a different point:

> The seed stays small because the complexity lives in the **rows**, not the **code**.

A minimal seed could be:
1. Create the SQLite schema (3 tables)
2. Insert bootstrap rows into `profiles`, `components`, `tools`
3. Run one query: `SELECT source FROM tools WHERE name = 'execute-phase'` — and execute the result

That's still ~50 lines of code. But the 50 lines don't define the system's limits. The rows do.

## The Real Claim to Fame

Not "look how little code it takes to build a state machine."

But: **"look how little code it takes to build a state machine that can describe, observe, and regenerate itself without changing the code."**

The minimal seed is a party trick. An evolvable system is the actual engineering win. Both are achievable — just not at the same time, and not by optimizing for the same thing.

---

*Spiral not yet closed. But the turn is visible.*
