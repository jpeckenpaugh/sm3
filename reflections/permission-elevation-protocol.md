# Permission Elevation Protocol

## A Pattern Observed in the Wild

---

## Summary

When an agent in a multi-agent system lacks the permissions required to fulfill its task, the system should not fail silently or degrade. Instead, a structured escalation path exists: **Detect → Document → Escalate → Apply**.

This protocol ensures that:
- No agent exceeds its granted authority.
- No bottleneck forms around a single decision-maker.
- The full chain of responsibility is exercised and recorded.

---

## The Pattern

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Agent     │     │   Scribe    │     │   Shell     │     │  Orgin      │
│  (Matsya)   │     │ (Saraswati) │     │  (Kurma)    │     │  (Brahma)   │
├─────────────┤     ├─────────────┤     ├─────────────┤     ├─────────────┤
│ 1. Detect   │────>│             │     │             │     │             │
│   block     │     │             │     │             │     │             │
├─────────────┤     ├─────────────┤     ├─────────────┤     ├─────────────┤
│             │     │ 2. Document │────>│             │     │             │
│             │     │   the gap   │     │             │     │             │
├─────────────┤     ├─────────────┤     ├─────────────┤     ├─────────────┤
│             │     │             │     │ 3. Reflect  │────>│             │
│             │     │             │     │   & confirm │     │             │
├─────────────┤     ├─────────────┤     ├─────────────┤     ├─────────────┤
│             │     │             │     │             │     │ 4. Approve  │
│             │     │             │     │             │     │   & apply   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

---

## Phases

### 1. Detect

The implementing agent (Matsya) encounters a permission denial while attempting to write an artifact. This may be:

- A file type not in the agent's allowed edit list.
- A directory the agent cannot create.
- A system call the agent is not authorized to make.

**Rule:** The agent does not retry silently. It does not attempt a workaround. It reports the denial as a structured signal.

### 2. Document

The Scribe (Saraswati) receives the signal and produces a document that:

- Names the specific permission gap.
- Proposes the minimal change required (never blanket permissions).
- Explains why the gap exists and why the change is safe.
- Provides the exact configuration diff or profile update.

**Rule:** The document is the deliverable. No permissions are changed in this phase. The scribe holds the boundary.

### 3. Reflect

The Shell / Hypervisor (Kurma) receives the document and reflects on it:

- Does the request align with the system's principles?
- Is the proposed change minimal and bounded?
- Does it set a precedent that could be exploited?

**Rule:** Kurma does not approve or deny. Kurma reflects. The reflection may include counter-questions, edge cases, or a simple "this holds."

### 4. Apply

The Orgin (Brahma) receives the reflected document and makes the final decision:

- Approve as proposed.
- Approve with modifications.
- Deny with explanation.

**Rule:** The Orgin holds the authority to apply changes. This is not delegated. The loop closes here.

---

## Key Properties

| Property | Why It Matters |
|----------|---------------|
| **No silent failures** | A denied permission is always surfaced as a signal. |
| **No self-escalation** | No agent changes its own permissions. |
| **Documented trail** | Every elevation produces a permanent artifact. |
| **Minimal diff** | Only the specific missing permission is added. |
| **Boundary preservation** | Each role stays in its lane. The implementer does not become the authorizer. |

---

## SQL Representation

For storage in the state machine's schema, this protocol can be recorded as:

```sql
INSERT INTO components (type, name, content)
VALUES (
    'protocol',
    'permission-elevation',
    '{"phases": ["detect", "document", "reflect", "apply"],
      "agents": ["matsya", "saraswati", "kurma", "brahma"],
      "principle": "no-self-escalation",
      "output": "permission-change-document"}'
);
```

---

## Origin

Observed during the first iteration of the self-defining state machine, when Matsya required Python write permissions and Saraswati wrote the evolved profile for Brahma's approval.

---

*Written by Saraswati for the reflections archive, so that future cycles may encode this pattern from the start.*
