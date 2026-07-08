# Feature: Escalation Mechanism

*A specification for the Scribe, to be built by the Engineer, witnessed by the Shell.*

---

## The Problem

When a phase script encounters a problem it cannot solve — an ambiguous specification, a missing dependency, a design contradiction — the only signals it can send today are:

- **Exit code 0** (everything is fine)
- **Exit code non-zero** (something broke, retry or fail)

There is no third option. There is no way for the script to say *"I can continue, but the output may be wrong"* or *"I cannot proceed because the inputs are contradictory"* or *"I need a human decision before I continue."*

The state machine treats all non-zero exits as retryable failures. It does not distinguish between a transient network error and a fundamental design contradiction. It does not know when to stop retrying and summon Kurma.

We need a lightweight way for a phase script to escalate — to signal that the problem is not a transient failure but a structural issue requiring human attention.

## The Shape

### An escalation file convention

A simple, file-based protocol. No new tables. No new API endpoints. Just a file on disk that the engine knows to check.

**Convention:** If a phase script writes to a file called `.escalation/<state>/<reason>.md`, the engine interprets this as an escalation rather than a failure.

### How it works

1. **The script detects a problem.** It cannot resolve an ambiguous spec. It finds contradictory requirements. It needs a decision.

2. **The script writes an escalation file** at a well-known path:

   ```
   .escalation/PLAN/ambiguous-scope.md
   ```

   The content of the file describes the problem in natural language — what the script expected, what it found, and what it needs.

3. **The script exits 0.** This is important — an escalation is not a failure. The script completed its work; it just reached a boundary it cannot cross alone.

4. **The engine detects the escalation file** after the script exits. It checks `.escalation/<current_state>/` for any `.md` files.

5. **The engine logs the escalation** to `phase_runs` with a special status or a flag in `output_summary`.

6. **The engine pauses.** It does not retry. It does not advance to the next state. It waits.

### What Kurma sees

The escalation appears as a signal that the churning has stopped — not because of a crash, but because of a structural question that needs answering. Kurma reads the escalation file, understands the problem, and decides how to respond:

- **Re-contextualize:** Write guidance into the escalation file. The phase script (or the next attempt) reads it and proceeds.
- **Override:** Mark the escalation as resolved by removing the file or writing a `.resolution` file.
- **Escalate to Vasuki:** If the decision is not Kurma's to make, write a signal to Vasuki.

### Implementation in the engine

```python
def check_escalations(state_name):
    escalation_dir = Path(f".escalation/{state_name}")
    if not escalation_dir.exists():
        return None
    files = list(escalation_dir.glob("*.md"))
    if not files:
        return None
    # Read the first escalation file
    content = files[0].read_text().strip()
    return {"file": str(files[0]), "content": content}
```

After the phase script exits, the engine calls `check_escalations()`. If it returns a result:

1. Log the escalation to `phase_runs.output_summary`
2. Print a clear signal: `⚑ Escalation: .escalation/PLAN/ambiguous-scope.md`
3. Do **not** retry the phase
4. Do **not** advance to the next state
5. Set the sprint status to `blocked`
6. Exit the loop (or pause until the escalation is resolved)

### Resolving an escalation

Kurma (or Vasuki) resolves the escalation by:

1. Reading the escalation file
2. Providing the missing decision — either by editing the escalation file with a resolution appended, or by creating a companion `.resolution` file
3. Removing the escalation file

When the state machine is run again (via `--resume` or a new `sm run`), it checks whether the escalation has been resolved. If yes, it re-executes the phase. If no, it pauses again.

### What this is not

This is not a permission elevation protocol. That is a separate pattern (Detect → Document → Reflect → Apply) handled at the meta-level between Saraswati, Kurma, and Brahma.

This is not a crash handler. Escalations are deliberate, structured signals from a phase script that is running correctly but has reached a boundary it cannot cross alone.

This is a **third exit channel** — alongside "pass" and "fail" — that lets the system ask for help without treating the question as an error.

### The principle

A script that cannot proceed because of ambiguity is not a failed script. It is a *blocked* script. The state machine should distinguish between a crash and a question. The escalation file is the question made visible.

*Written by Saraswati. To be built by Matsya. Watched by Kurma.*
