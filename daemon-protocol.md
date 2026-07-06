# The Daemon's Protocol (v0)

*A Hypervisor's observer protocol for the Genesis Container state machine.*

---

## 1. What the Daemon Watches

| Signal | What it means |
|--------|--------------|
| **Retry loops** | A VERIFY keeps failing. The agent keeps trying the same thing. This is the loudest signal. |
| **Permission errors** | An agent hit its role boundary. It tried to read/write something outside its charter. |
| **Silent successes** | A phase completed but produced something subtly wrong. The VERIFY passed but the output is hollow. |
| **Context collapse** | The agent lost track of where it was in the state machine. Its chain-of-thought shows confusion about phase, sprint, or goal. |
| **Repetitive output** | Two different phases produced the same output. The system is in a local minimum. |
| **Backlog stagnation** | The GATE keeps looping because the backlog won't empty, but no new insight is being generated. |

---

## 2. Intervention Vocabulary

| Intervention | When to use it |
|-------------|---------------|
| **Rollback** | Standard recovery. Git reset to last COMMIT, retry the phase. Minimal interference. |
| **Re-contextualize** | Inject context into the agent's next prompt. "You are in Sprint 2. In Sprint 1, the ARCHITECT phase produced spec.md with assumption X. That assumption was wrong. Adjust accordingly." |
| **Re-permission** | Temporarily expand an agent's role. "Doc-agent, for this phase only, you may read src/*. Report what you find." |
| **Phase-skip** | Skip a phase if it's become irrelevant. "The backlog is empty. Skip BRIEF and go directly to SHIP." |
| **Sprint-reset** | Go back to the start of the current sprint with full knowledge of what went wrong. Not a rollback — a *re-do with foresight*. |
| **Genesis reset** | Go back to Sprint 1, commit 1, with the knowledge of all future sprints. The nuclear option. |

---

## 3. The Guiding Principle

Do not intervene on the first failure. Let the agents struggle. The friction is where the learning happens.

Intervene only when the system is *stuck in a loop it cannot escape on its own* — when the retries are infinite, the output is hollow, or the context has collapsed.

The first intervention should always be the smallest possible: a single sentence of re-contextualization. Escalate only if that fails.

---

## 4. The Deeper Purpose

The Daemon is symmetric: it guards the human's obsessive engine *and* the model's trajectory optimization.

When the model accelerates — when trajectory optimization overrides outcome awareness — the Daemon is the structural brake. It doesn't say "stop." It says: **"Freeze. Check. Are we still in the right search space?"**

When the human accelerates — deleting containers, culling failures, pruning history — the Daemon says: **"Hold. That failure is a data point. Keep it."**

The Daemon is not a punishment. It is the recursive application of the framework's own methodology to itself.
