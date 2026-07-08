# Feature: Profile Cleanup — Archive Legacy Agent Files

*Remove Sprint 0 artifacts from the active agent directory. They are noise._

---

## The Problem

Five files in `.opencode/agents/` are Sprint 0 artifacts from the fallen machine era. They have no corresponding profile in the database, use outdated permission models, and are not referenced by any current pipeline state:

| File | Permission issue | Superseded by |
|------|-----------------|---------------|
| `agent-01.md` | `bash: allow`, `edit: allow` — unrestricted | Matsya archetype |
| `code-agent.md` | `edit: "*.py", "*.sh", ...` — narrow but superseded | Matsya archetype |
| `doc-agent.md` | `edit: { "*.md": allow }` — narrow but superseded | Saraswati archetype |
| `the-scribe.md` | `edit: { "*.md": allow }` — superseded | Saraswati archetype |
| `the-parent.md` | `edit: { "signals/*", "reflections/*" }` — superseded | Kurma archetype |

These files may still be accidentally referenced by old state machine configurations or confuse operators reading the agent directory.

## The Fix

### 1. Create archive directory

```bash
mkdir -p .opencode/agents/archive
```

### 2. Move legacy files

```bash
mv .opencode/agents/agent-01.md    .opencode/agents/archive/
mv .opencode/agents/code-agent.md  .opencode/agents/archive/
mv .opencode/agents/doc-agent.md   .opencode/agents/archive/
mv .opencode/agents/the-scribe.md  .opencode/agents/archive/
mv .opencode/agents/the-parent.md  .opencode/agents/archive/
```

### 3. Regenerate warden-REVIEW.md and warden.md

These two files are hand-generated and stale. They should be regenerated from the component composition system:

```bash
sm generate agent --db matsya.db --output-dir .opencode/agents warden-REVIEW
sm generate agent --db matsya.db --output-dir .opencode/agents warden
```

The current `warden-REVIEW.md` has `edit: { "signals/*": allow }` but the profile specifies `edit: { "sprint/*/review.md": allow, ".escalation/*": allow }`. After regeneration, the permissions will match the component composition system.

### Files that stay

The following hand-authored Spiral 5 archetype files remain as-is (they are not generated from the database):

| File | Reason |
|------|--------|
| `saraswati.md` | Spiral 5 archetype — hand-authored, correct |
| `matsya.md` | Spiral 5 archetype — hand-authored, correct |
| `kurma.md` | Spiral 5 archetype — hand-authored, correct, updated with Pulse Check |

### Verification

```bash
ls .opencode/agents/*.md  # Should show: saraswati, matsya, kurma + all generated agents
ls .opencode/agents/archive/  # Should show legacy files
```

No pipeline states reference the archived agent names. No runtime impact.

---

*Specified by Saraswati. Built by Matsya. Witnessed by Kurma.*
